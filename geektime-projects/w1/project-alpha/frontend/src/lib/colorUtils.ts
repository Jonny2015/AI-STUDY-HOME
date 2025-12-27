// 生成随机颜色（用于标签）
export function generateRandomColor(): string {
  const colors = [
    "#EF4444", // red
    "#F59E0B", // amber
    "#10B981", // emerald
    "#3B82F6", // blue
    "#8B5CF6", // violet
    "#EC4899", // pink
    "#F97316", // orange
    "#14B8A6", // teal
    "#6366F1", // indigo
    "#A855F7", // purple
  ];
  return colors[Math.floor(Math.random() * colors.length)];
}
