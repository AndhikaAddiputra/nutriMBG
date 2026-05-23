import { Progress, Typography } from 'antd';

const { Text } = Typography;

interface ScoreGaugeProps {
  score: number;
}

export function ScoreGauge({ score }: ScoreGaugeProps) {
  let color = '#4CAF50';
  let grade = 'A';
  if (score < 50) { color = '#F44336'; grade = 'C'; }
  else if (score < 80) { color = '#FF9800'; grade = 'B'; }

  return (
    <div style={{ textAlign: 'center' }}>
      <Progress
        type="dashboard"
        percent={score}
        strokeColor={color}
        format={(percent) => (
          <div>
            <div style={{ fontSize: 32, fontWeight: 'bold', color }}>{grade}</div>
            <div style={{ fontSize: 16, color: '#666' }}>{percent}/100</div>
          </div>
        )}
      />
      <div style={{ marginTop: 8 }}>
        <Text strong>Skor Gizi</Text>
      </div>
    </div>
  );
}
