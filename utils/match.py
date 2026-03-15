import cv2
import numpy as np
import math
import pandas as pd
from sklearn.neighbors import NearestNeighbors, KDTree
from pathlib import Path


# =========================================================
# 路径配置
# =========================================================
ROOT = Path(__file__).resolve().parent
SRC_PATH = ROOT / "images" / "origin" / "1.png"
TGT_PATH = ROOT / "images" / "solution" / "2.png"
OUT_DIR = ROOT / "results"
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUT_OVERLAY = OUT_DIR / "aligned_overlay.png"
OUT_OVERLAY2 = OUT_DIR / "aligned_overlay_2.png"
OUT_CSV = OUT_DIR / "dot_match_results.csv"
OUT_HOLES_BLUE = OUT_DIR / "debug_holes_blue.png"
OUT_RED_MASK = OUT_DIR / "debug_red_mask.png"

OUT_BOUNDARY_CSV = OUT_DIR / "boundary_pause_points.csv"
OUT_BOUNDARY_VIS = OUT_DIR / "boundary_verification.png"
# ✅ 追加两个原始图坐标文件
OUT_BLUE_SRC_CSV = OUT_DIR / "blue_points_in_source.csv"
OUT_BLUE_SRC_CSV_2 = OUT_DIR / "blue_points_in_source_2.csv" # <-- 新追加

tol = 6.0

# =============== 1) 读图 ===============
src = cv2.imread(str(SRC_PATH), cv2.IMREAD_UNCHANGED)
tgt = cv2.imread(str(TGT_PATH), cv2.IMREAD_UNCHANGED)

if src is None: raise FileNotFoundError(f"读不到原始图片: {SRC_PATH}")
if tgt is None: raise FileNotFoundError(f"读不到答案图片: {TGT_PATH}")

if src.ndim == 2: src_bgr = cv2.cvtColor(src, cv2.COLOR_GRAY2BGR)
else: src_bgr = src[:, :, :3]

if tgt.ndim == 2: tgt_bgr = cv2.cvtColor(tgt, cv2.COLOR_GRAY2BGR)
else: tgt_bgr = tgt[:, :, :3]

tgt_gray = cv2.cvtColor(tgt_bgr, cv2.COLOR_BGR2GRAY)
H, W = tgt_gray.shape

# =============== 2) 提取原图红点中心 ===============
hsv = cv2.cvtColor(src_bgr, cv2.COLOR_BGR2HSV)
lower1 = np.array([0, 80, 80]);   upper1 = np.array([10, 255, 255])
lower2 = np.array([170, 80, 80]); upper2 = np.array([180, 255, 255])
mask_red = cv2.inRange(hsv, lower1, upper1) | cv2.inRange(hsv, lower2, upper2)
mask_red = cv2.medianBlur(mask_red, 3)
cv2.imwrite(str(OUT_RED_MASK), mask_red)

num, labels, stats, centroids = cv2.connectedComponentsWithStats(mask_red)
src_pts = centroids[1:]

# =============== 3) 提取答案图空隙中心 ===============
blur = cv2.GaussianBlur(tgt_gray, (0, 0), 1.0)
kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
tophat = cv2.morphologyEx(blur, cv2.MORPH_TOPHAT, kernel)
_, th = cv2.threshold(tophat, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
th = cv2.medianBlur(th, 3)

num2, labels2, stats2, centroids2 = cv2.connectedComponentsWithStats(th)
tgt_pts = centroids2[1:]
dist_map = cv2.distanceTransform(255 - th, cv2.DIST_L2, 3)

# =============== 4) 估计缩放 ===============
def median_spacing(pts: np.ndarray) -> float:
    nbrs = NearestNeighbors(n_neighbors=2).fit(pts)
    d, _ = nbrs.kneighbors(pts)
    return float(np.median(d[:, 1]))

s_src = median_spacing(src_pts)
s_tgt = median_spacing(tgt_pts)
scale = s_tgt / s_src

src_center = src_pts.mean(axis=0)
tgt_center = tgt_pts.mean(axis=0)
base_trans = (tgt_center[0] - src_center[0], tgt_center[1] - src_center[1])

# =============== 5) 变换函数 ===============
def transform_points(pts, scale=1.0, angle_deg=0.0, translation=(0.0, 0.0), center=None):
    pts = np.asarray(pts, dtype=np.float32)
    if center is None: center = pts.mean(axis=0)
    ang = math.radians(angle_deg)
    R = np.array([[math.cos(ang), -math.sin(ang)], [math.sin(ang), math.cos(ang)]], dtype=np.float32)
    out = (pts - center) * scale
    out = out @ R.T + center + np.array(translation, dtype=np.float32)
    return out

# =============== 6) 配准优化 ===============
tgt_tree = KDTree(tgt_pts)
def icp_translation(src_trans, max_iter=20, thresh=15):
    trans = np.array([0.0, 0.0], dtype=np.float32)
    pts = src_trans.copy()
    for _ in range(max_iter):
        dist, ind = tgt_tree.query(pts, k=1)
        dist, ind = dist[:, 0], ind[:, 0]
        inl = dist < thresh
        if int(inl.sum()) < 50: break
        delta = np.median(tgt_pts[ind[inl]] - pts[inl], axis=0)
        pts += delta
        trans += delta
        if float(np.linalg.norm(delta)) < 0.1: break
    dist2, _ = tgt_tree.query(pts, k=1)
    return trans, pts, float(np.median(dist2))

best = None
for ang in np.linspace(-180, 180, 1441):
    pts0 = transform_points(src_pts, scale=scale, angle_deg=float(ang), translation=base_trans, center=src_center)
    delta, pts_aligned, meddist = icp_translation(pts0, thresh=15)
    if best is None or meddist < best[0]: best = (meddist, float(ang), delta, pts_aligned)

_, best_ang, best_delta, pts_final = best

def score_shift(pts, dx, dy):
    xs, ys = np.round(pts[:, 0] + dx).astype(int), np.round(pts[:, 1] + dy).astype(int)
    inb_local = (xs >= 0) & (xs < W) & (ys >= 0) & (ys < H)
    dtmp = np.full(len(xs), np.inf, dtype=np.float32)
    dtmp[inb_local] = dist_map[ys[inb_local], xs[inb_local]]
    hit = (dtmp <= tol)
    return int(hit.sum()), float(np.nansum(dtmp[hit]))

best_dx, best_dy, best_hit, best_sum = 0, 0, -1, 1e30
for dy in range(-30, 31, 2):
    for dx in range(-30, 31, 2):
        hit, s = score_shift(pts_final, dx, dy)
        if hit > best_hit or (hit == best_hit and s < best_sum): best_hit, best_sum, best_dx, best_dy = hit, s, dx, dy

best_offset = np.array([best_dx, best_dy], dtype=np.float32)
pts_final += best_offset

# =============== 7) 命中判定 ===============
xs, ys = np.round(pts_final[:, 0]).astype(int), np.round(pts_final[:, 1]).astype(int)
inb = (xs >= 0) & (xs < W) & (ys >= 0) & (ys < H)
d = np.full(len(xs), np.inf, dtype=np.float32)
d[inb] = dist_map[ys[inb], xs[inb]]
matched = d <= tol

# =============== 8) 导出 7 列 CSV ===============
pd.DataFrame({
    "src_index": range(len(src_pts)),
    "src_x": src_pts[:, 0],
    "src_y": src_pts[:, 1],
    "tgt_x": pts_final[:, 0],
    "tgt_y": pts_final[:, 1],
    "dist_to_hole_px": d,
    "matched": matched
}).to_csv(str(OUT_CSV), index=False)

# =============== 9) 生成 PNG 结果 ===============
overlay = tgt_bgr.copy()
for (px, py), m in zip(pts_final, matched):
    color = (0, 255, 255) if m else (0, 0, 255)
    cv2.circle(overlay, (int(round(px)), int(round(py))), 3, color, -1)
cv2.imwrite(str(OUT_OVERLAY), overlay)

overlay2 = tgt_bgr.copy()
for (px, py), m in zip(pts_final, matched):
    if m: cv2.circle(overlay2, (int(round(px)), int(round(py))), 3, (0, 255, 255), -1)
cv2.imwrite(str(OUT_OVERLAY2), overlay2)

debug_holes = tgt_bgr.copy()
for (hx, hy) in tgt_pts:
    cv2.circle(debug_holes, (int(round(hx)), int(round(hy))), 3, (255, 0, 0), -1)
cv2.imwrite(str(OUT_HOLES_BLUE), debug_holes)

# =========================================================
# ✅ 10) 任务规划：边界提取与逆向坐标计算 (核心追加逻辑)
# =========================================================
yellow_pts = pts_final[matched]
if len(yellow_pts) > 0:
    b_mask = np.zeros((H, W), dtype=np.uint8)
    r_val = int(round(s_tgt * 0.8))
    for pt in yellow_pts:
        cv2.circle(b_mask, (int(round(pt[0])), int(round(pt[1]))), r_val, 255, -1)
    
    k_size = int(round(s_tgt * 2.5))
    if k_size % 2 == 0: k_size += 1
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k_size, k_size))
    b_mask = cv2.morphologyEx(b_mask, cv2.MORPH_CLOSE, k)
    
    cnts, _ = cv2.findContours(b_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if cnts:
        main_c = max(cnts, key=cv2.contourArea)
        approx = cv2.approxPolyDP(main_c, 2.5, True)
        blue_pause_pts = approx.reshape(-1, 2).astype(np.float32)
        
        # --- 新增：逆向变换逻辑 (设计稿 -> 原始图) ---
        # 1. 计算总平移量
        total_trans = best_delta + base_trans + best_offset
        # 2. 准备逆向旋转 (角度取负值，用于完全还原)
        ang_inv = math.radians(-best_ang)
        R_inv = np.array([
            [math.cos(ang_inv), -math.sin(ang_inv)],
            [math.sin(ang_inv), math.cos(ang_inv)]
        ], dtype=np.float32)
        
        # 3. 执行逆变换计算
        # 计算去平移后的临时坐标
        temp_pts = blue_pause_pts - total_trans - src_center
        
        # 方案1：完全还原坐标 (Undo Translation, Undo Rotation, Undo Scale)
        pts_in_src = (temp_pts @ R_inv.T) / scale + src_center
        
        # 方案2：保留顺时针旋转104度状态的原始图空间坐标
        # (Undo Translation, Undo Scale, BUT KEEP THE ROTATION relative to source center)
        pts_in_src_2 = (temp_pts / scale) + src_center
        
        # 保存两个 CSV
        pd.DataFrame(pts_in_src, columns=["src_x", "src_y"]).to_csv(str(OUT_BLUE_SRC_CSV), index=False)
        pd.DataFrame(pts_in_src_2, columns=["src_x", "src_y"]).to_csv(str(OUT_BLUE_SRC_CSV_2), index=False)
        # ----------------------------------------

        # 保持原有的紫色锚点生成逻辑
        margin = 5
        purple_anchors = np.array([
            [margin, margin], [W - margin, margin], [margin, H - margin],
            [W - margin, H - margin], [margin, H // 2], [W - margin, H // 2]
        ], dtype=np.int32)
        
        df_blue = pd.DataFrame(blue_pause_pts, columns=["x", "y"])
        df_blue["type"] = "blue_boundary"
        df_purple = pd.DataFrame(purple_anchors, columns=["x", "y"])
        df_purple["type"] = ["purple_TL", "purple_TR", "purple_BL", "purple_BR", "purple_ML", "purple_MR"]
        pd.concat([df_blue, df_purple]).to_csv(str(OUT_BOUNDARY_CSV), index=False)
        
        vis_b = overlay2.copy()
        cv2.polylines(vis_b, [approx], isClosed=True, color=(0, 255, 0), thickness=2)
        for (bx, by) in blue_pause_pts:
            cv2.circle(vis_b, (int(bx), int(by)), 5, (255, 0, 0), -1)
        for (px, py) in purple_anchors:
            cv2.circle(vis_b, (int(px), int(py)), 8, (255, 0, 255), -1)
        cv2.imwrite(str(OUT_BOUNDARY_VIS), vis_b)




# ... 保持原有代码不变 ...
# 在最后 11 步报告之前添加：

# with open(OUT_DIR / "angle.txt", "w") as f:
#     f.write(str(best_ang))


# 如果角度小于0，则存储 360 + best_ang (即 360 - |best_ang|)
angle_to_save = 360 + best_ang if best_ang < 0 else best_ang

with open(OUT_DIR / "angle.txt", "w") as f:
    f.write(str(angle_to_save))
# ... 后面保持原有打印报告的代码 ...



# =============== 11) 终端报告 (增强版) ===============
print("\n" + "="*50)
print("             点云配准与边界提取报告")
print("="*50)
print(f"1. 图像信息:")
print(f"   - 原始图: {SRC_PATH.name} ({src.shape[1]}x{src.shape[0]})")
print(f"   - 答案图: {TGT_PATH.name} ({W}x{H})")
print(f"\n2. 关键配准参数:")
print(f"   - 旋转角度 (Best Angle): {best_ang:.4f} 度")
print(f"   - 缩放比例 (Scale): {scale:.4f}")
print(f"   - 基础平移 (Base Trans): x={base_trans[0]:.2f}, y={base_trans[1]:.2f}")
print(f"   - 最终微调 (Fine Tune): dx={best_dx}, dy={best_dy}")
print(f"\n3. 文件保存路径:")
print(f"   - [CSV] 点分类数据: {OUT_CSV}")
print(f"   - [CSV] 设计稿坐标(蓝+紫): {OUT_BOUNDARY_CSV}")
print(f"   - [CSV] 原始图坐标(完全还原): {OUT_BLUE_SRC_CSV}")
print(f"   - [CSV] 原始图坐标(保留旋转版本): {OUT_BLUE_SRC_CSV_2}  <-- NEW!") # 追加信息
print(f"   - [PNG] 红黄叠加图: {OUT_OVERLAY}")
print(f"   - [PNG] 纯黄色点图: {OUT_OVERLAY2}")
print(f"   - [PNG] 蓝色空隙图: {OUT_HOLES_BLUE}")
print(f"   - [PNG] 红色掩模图: {OUT_RED_MASK}")
print(f"   - [PNG] 边界验证图: {OUT_BOUNDARY_VIS}")
print(f"\n4. 统计结果:")
print(f"   - 识别红点总数: {len(src_pts)}")
print(f"   - 成功匹配(黄点): {matched.sum()}")
print(f"   - 匹配失败(红点): {len(src_pts) - matched.sum()}")
print(f"   - 边界蓝色点数: {len(blue_pause_pts) if 'blue_pause_pts' in locals() else 0}")
print("="*50 + "\n")



