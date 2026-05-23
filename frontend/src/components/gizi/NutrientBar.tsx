import { Progress, Typography, Row, Col } from 'antd';

const { Text } = Typography;

interface NutrientBarProps {
  label: string;
  icon: string;
  percent: number;
}

export function NutrientBar({ label, icon, percent }: NutrientBarProps) {
  let color = '#4CAF50'; // Green if sufficient
  if (percent < 50) color = '#F44336'; // Red if very low
  else if (percent < 80) color = '#FF9800'; // Orange if moderate
  else if (percent > 120) color = '#FF9800'; // Orange if excessive

  return (
    <Row align="middle" style={{ marginBottom: 12 }}>
      <Col span={8}>
        <Text>{icon} {label}</Text>
      </Col>
      <Col span={16}>
        <Progress 
          percent={percent > 100 ? 100 : percent} 
          strokeColor={color} 
          format={() => `${Math.round(percent)}%`} 
        />
      </Col>
    </Row>
  );
}
