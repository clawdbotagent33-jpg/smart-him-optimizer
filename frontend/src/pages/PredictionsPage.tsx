/**
 * AI 예측 페이지
 */
import React, { useState } from 'react';
import {
  Card,
  Form,
  Input,
  Select,
  InputNumber,
  Button,
  Space,
  Divider,
  Tag,
  Alert,
} from 'antd';
import { PlusOutlined, MinusCircleOutlined, ExperimentOutlined } from '@ant-design/icons';
import { useMutation } from '@tanstack/react-query';
import { predictionsApi, PredictionRequest, PredictionResponse } from '../services/api';
import PredictionResultCard from '../components/PredictionResultCard';

const { TextArea } = Input;
const { Option } = Select;

const PredictionsPage: React.FC = () => {
  const [form] = Form.useForm();
  const [predictionResult, setPredictionResult] = useState<PredictionResponse | null>(null);

  const predictMutation = useMutation({
    mutationFn: (data: PredictionRequest) => predictionsApi.predictComprehensive(data),
    onSuccess: (response) => {
      setPredictionResult(response);
    },
  });

  interface FormValues {
    principalDiagnosis: string;
    secondaryDiagnoses?: string[];
    procedures?: string[];
    age?: number;
    gender?: string;
    department?: string;
    lengthOfStay?: number;
    clinicalNotes?: string;
  }

  const onFinish = (values: FormValues) => {
    const requestData: PredictionRequest = {
      principalDiagnosis: values.principalDiagnosis,
      secondaryDiagnoses: values.secondaryDiagnoses || [],
      procedures: values.procedures || [],
      age: values.age,
      gender: values.gender,
      department: values.department,
      lengthOfStay: values.lengthOfStay,
      clinicalNotes: values.clinicalNotes,
    };

    setPredictionResult(null);
    predictMutation.mutate(requestData);
  };

  const isPending = predictMutation.status === 'pending';

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <Card title="AI 기반 K-DRG 예측" extra={<ExperimentOutlined />}>
          <Form
            form={form}
            layout="vertical"
            onFinish={onFinish}
            initialValues={{
              secondaryDiagnoses: [''],
              procedures: [''],
            }}
          >
            <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
              <div style={{ flex: 1, minWidth: 200 }}>
                <Form.Item
                  label="주진단 (KCD-9 코드)"
                  name="principalDiagnosis"
                  rules={[{ required: true, message: '주진단 코드를 입력해주세요' }]}
                >
                  <Input placeholder="예: I50 (심부전)" />
                </Form.Item>
              </div>

              <div style={{ flex: 1, minWidth: 150 }}>
                <Form.Item label="부서" name="department">
                  <Select placeholder="선택해주세요" allowClear>
                    <Option value="내과">내과</Option>
                    <Option value="외과">외과</Option>
                    <Option value="정형외과">정형외과</Option>
                    <Option value="신경과">신경과</Option>
                    <Option value="순환기내과">순환기내과</Option>
                  </Select>
                </Form.Item>
              </div>

              <div style={{ width: 100 }}>
                <Form.Item label="나이" name="age">
                  <InputNumber placeholder="세" style={{ width: '100%' }} min={0} max={120} />
                </Form.Item>
              </div>

              <div style={{ width: 100 }}>
                <Form.Item label="성별" name="gender">
                  <Select placeholder="선택" allowClear>
                    <Option value="M">남</Option>
                    <Option value="F">여</Option>
                  </Select>
                </Form.Item>
              </div>

              <div style={{ width: 100 }}>
                <Form.Item label="재원일수" name="lengthOfStay">
                  <InputNumber placeholder="일" style={{ width: '100%' }} min={0} />
                </Form.Item>
              </div>
            </div>

            <Form.Item label="부진단 (KCD-9 코드)">
              <Form.List name="secondaryDiagnoses">
                {(fields, { add, remove }) => (
                  <>
                    {fields.map((field, index) => (
                      <Space key={field.key} style={{ display: 'flex', marginBottom: 8 }}>
                        <Form.Item
                          {...field}
                          style={{ margin: 0, flex: 1 }}
                          rules={[{ required: false }]}
                        >
                          <Input placeholder={`부진단 ${index + 1}`} />
                        </Form.Item>
                        {fields.length > 1 && (
                          <Button
                            type="text"
                            danger
                            icon={<MinusCircleOutlined />}
                            onClick={() => remove(field.name)}
                          />
                        )}
                      </Space>
                    ))}
                    <Button
                      type="dashed"
                      onClick={() => add()}
                      block
                      icon={<PlusOutlined />}
                    >
                      부진단 추가
                    </Button>
                  </>
                )}
              </Form.List>
            </Form.Item>

            <Form.Item label="처치/시술">
              <Form.List name="procedures">
                {(fields, { add, remove }) => (
                  <>
                    {fields.map((field, index) => (
                      <Space key={field.key} style={{ display: 'flex', marginBottom: 8 }}>
                        <Form.Item
                          {...field}
                          style={{ margin: 0, flex: 1 }}
                          rules={[{ required: false }]}
                        >
                          <Input placeholder={`처치 ${index + 1}`} />
                        </Form.Item>
                        {fields.length > 1 && (
                          <Button
                            type="text"
                            danger
                            icon={<MinusCircleOutlined />}
                            onClick={() => remove(field.name)}
                          />
                        )}
                      </Space>
                    ))}
                    <Button
                      type="dashed"
                      onClick={() => add()}
                      block
                      icon={<PlusOutlined />}
                    >
                      처치 추가
                    </Button>
                  </>
                )}
              </Form.List>
            </Form.Item>

            <Form.Item label="임상 노트 (선택사항)" name="clinicalNotes">
              <TextArea
                rows={3}
                placeholder="임상적 특이사항, 합병증 등 추가 정보를 입력해주세요"
              />
            </Form.Item>

            <Form.Item>
              <Button
                type="primary"
                htmlType="submit"
                loading={isPending}
                size="large"
                block
              >
                AI 예측 실행
              </Button>
            </Form.Item>
          </Form>
        </Card>
      </div>

      {predictionResult && (
        <PredictionResultCard result={predictionResult} />
      )}

      <Divider />

      <Card title="예측 기능 안내">
        <Alert
          message="K-DRG v4.7 기준 예측"
          description="AI 모델은 주진단, 부진단, 처치 정보를 분석하여 K-DRG 그룹(A/B/C)을 예측하고, A그룹 전환 가능성과 청구 삭감 위험도를 평가합니다."
          type="info"
          showIcon
        />
        <div style={{ marginTop: 16 }}>
          <Space direction="vertical" style={{ width: '100%' }}>
            <div><Tag color="success">A그룹 (전문질병군)</Tag> - 높은 CMI 가중치, 적극적인 코딩 권장</div>
            <div><Tag color="processing">B그룹 (일반질병군)</Tag> - 표준 CMI 가중치</div>
            <div><Tag color="warning">C그룹 (심층질병군)</Tag> - 낮은 CMI 가중치, 코딩 검토 필요</div>
          </Space>
        </div>
      </Card>
    </div>
  );
};

export default PredictionsPage;
