/**
 * Velocímetro visual que traduz o score (-100 a +100) em compra/neutro/venda.
 * Inspirado em gauges de dashboards profissionais.
 */

interface ScoreGaugeProps {
  score: number;
  signal: string;
  size?: number;
}

export function ScoreGauge({ score, signal, size = 160 }: ScoreGaugeProps) {
  // Normaliza score de -100..+100 para 0..1
  const normalized = (score + 100) / 200;
  // Ângulo: -135° (venda forte) a +135° (compra forte)
  const angle = -135 + normalized * 270;

  const radius = size / 2 - 10;
  const cx = size / 2;
  const cy = size / 2;

  // Cor baseada no score
  const getColor = () => {
    if (score >= 30) return "#10b981";
    if (score <= -30) return "#ef4444";
    return "#6b7280";
  };

  // Arco de fundo
  const describeArc = (startAngle: number, endAngle: number, r: number) => {
    const start = polarToCartesian(cx, cy, r, endAngle);
    const end = polarToCartesian(cx, cy, r, startAngle);
    const largeArcFlag = endAngle - startAngle <= 180 ? "0" : "1";
    return `M ${start.x} ${start.y} A ${r} ${r} 0 ${largeArcFlag} 0 ${end.x} ${end.y}`;
  };

  const polarToCartesian = (
    centerX: number,
    centerY: number,
    r: number,
    angleDeg: number
  ) => {
    const rad = ((angleDeg - 90) * Math.PI) / 180;
    return {
      x: centerX + r * Math.cos(rad),
      y: centerY + r * Math.sin(rad),
    };
  };

  // Ponteiro
  const pointerEnd = polarToCartesian(cx, cy, radius - 15, angle);
  const color = getColor();

  return (
    <div className="flex flex-col items-center gap-2">
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        {/* Arco de fundo */}
        <path
          d={describeArc(-135, 135, radius)}
          fill="none"
          stroke="#374151"
          strokeWidth={8}
          strokeLinecap="round"
        />

        {/* Zona verde (compra) */}
        <path
          d={describeArc(45, 135, radius)}
          fill="none"
          stroke="#10b981"
          strokeWidth={8}
          strokeLinecap="round"
          opacity={0.25}
        />

        {/* Zona vermelha (venda) */}
        <path
          d={describeArc(-135, -45, radius)}
          fill="none"
          stroke="#ef4444"
          strokeWidth={8}
          strokeLinecap="round"
          opacity={0.25}
        />

        {/* Ponteiro */}
        <line
          x1={cx}
          y1={cy}
          x2={pointerEnd.x}
          y2={pointerEnd.y}
          stroke={color}
          strokeWidth={3}
          strokeLinecap="round"
        />

        {/* Centro */}
        <circle cx={cx} cy={cy} r={6} fill={color} />
        <circle cx={cx} cy={cy} r={3} fill="#111827" />

        {/* Score numérico */}
        <text
          x={cx}
          y={cy + 30}
          textAnchor="middle"
          fill={color}
          fontSize={24}
          fontWeight="bold"
        >
          {score > 0 ? `+${score.toFixed(0)}` : score.toFixed(0)}
        </text>
      </svg>

      <span
        className={`badge ${
          signal === "COMPRA"
            ? "badge-compra"
            : signal === "VENDA"
              ? "badge-venda"
              : "badge-neutro"
        }`}
      >
        {signal}
      </span>
    </div>
  );
}
