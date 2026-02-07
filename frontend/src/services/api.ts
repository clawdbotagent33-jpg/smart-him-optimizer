/**
 * API 클라이언트 - 향상된 에러 처리
 */
import axios, { AxiosInstance, AxiosRequestConfig, AxiosError } from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || '/api/v1';

// API 에러 타입
export class ApiError extends Error {
  constructor(
    message: string,
    public statusCode: number,
    public code?: string,
    public details?: Record<string, string[]>
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

// API 응답 타입
export interface ApiResponse<T = unknown> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

// 에러 응답 타입
export interface ErrorResponse {
  detail?: string;
  message?: string;
  error?: string;
  code?: string;
  errors?: Record<string, string[]>;
}

// 인증 관련 타입
export interface LoginRequest {
  username: string;
  password: string;
}

export interface User {
  id: number;
  username: string;
  email: string;
  name: string;
  role: string;
  department?: string;
  isActive: boolean;
  createdAt: string;
}

export interface AuthResponse {
  accessToken: string;
  tokenType: string;
  user: User;
}

// 입원 관련 타입
export interface Admission {
  id: number;
  anonymousId?: string;
  admissionId: string;
  admissionDate: string;
  dischargeDate?: string;
  department: string;
  principalDiagnosis: string;
  secondaryDiagnoses?: string[];
  procedures?: string[];
  drgCode?: string;
  drgGroup?: string;
  drgWeight?: number;
  lengthOfStay?: number;
  claimAmount?: number;
  adjustedAmount?: number;
  denialReason?: string;
  createdAt: string;
}

export interface PredictionRequest {
  principalDiagnosis: string;
  secondaryDiagnoses?: string[];
  procedures?: string[];
  age?: number;
  gender?: string;
  department?: string;
  lengthOfStay?: number;
  clinicalNotes?: string;
}

export interface GroupPrediction {
  admissionId?: string;
  predictedGroup: string;
  probabilities: Record<string, number>;
  aGroupProbability: number;
  canUpgrade: boolean;
  confidence: number;
}

export interface DenialRisk {
  denialProbability: number;
  riskLevel: 'HIGH' | 'MEDIUM' | 'LOW';
  riskFactors: string[];
}

export interface UpgradeSuggestion {
  type: 'diagnosis' | 'procedure' | 'documentation';
  priority: 'high' | 'medium' | 'low';
  description: string;
  expectedImpact?: number;
}

export interface PredictionResponse {
  admissionId?: string;
  groupPrediction: GroupPrediction;
  denialRisk: DenialRisk;
  upgradeSuggestions?: UpgradeSuggestion[];
  recommendations: string[];
}

// 대시보드 타입
export interface DashboardMetrics {
  totalAdmissions: number;
  averageCmi: number;
  groupDistribution: Record<string, number>;
  denialRate: number;
  aGroupRatio: number;
}

export interface GroupDistribution {
  dates: string[];
  series: {
    A: number[];
    B: number[];
    C: number[];
  };
}

export interface TopDiagnoses {
  diagnoses: Array<{
    code: string;
    count: number;
    avg_weight: number;
  }>;
}

export interface ComplianceReport {
  admissionId: string;
  isCompliant: boolean;
  complianceReport: string;
  suggestedCodes: string[];
}

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // 요청 인터셉터 (토큰 추가)
    this.client.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // 응답 인터셉터 (향상된 에러 처리)
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError<ErrorResponse>) => {
        const errorResponse = error.response?.data;
        const statusCode = error.response?.status || 500;
        
        // 401: 인증 오류 - 로그인 페이지로 리다이렉트
        if (statusCode === 401) {
          localStorage.removeItem('token');
          localStorage.removeItem('user');
          window.location.href = '/login';
        }
        
        // 상세 에러 메시지 생성
        let errorMessage = errorResponse?.detail || 
                          errorResponse?.message || 
                          errorResponse?.error ||
                          '요청 처리 중 오류가 발생했습니다';
        
        // 에러 코드 매핑
        const errorCode = errorResponse?.code;
        
        // ApiError 객체 생성하여 reject
        const apiError = new ApiError(
          errorMessage,
          statusCode,
          errorCode,
          errorResponse?.errors
        );
        
        return Promise.reject(apiError);
      }
    );
  }

  async get<T = unknown>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.get<T>(url, config);
    return response.data;
  }

  async post<T = unknown>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.post<T>(url, data, config);
    return response.data;
  }

  async put<T = unknown>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.put<T>(url, data, config);
    return response.data;
  }

  async delete<T = unknown>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.delete<T>(url, config);
    return response.data;
  }

  // 파일 업로드
  async uploadFile<T = unknown>(url: string, file: File, additionalData?: Record<string, string | undefined>): Promise<T> {
    const formData = new FormData();
    formData.append('file', file);
    if (additionalData) {
      Object.entries(additionalData).forEach(([key, value]) => {
        if (value !== undefined) {
          formData.append(key, value);
        }
      });
    }

    const response = await this.client.post<T>(url, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  }
}

// API 서비스
export const api = new ApiClient();

// 인증 API
export const authApi = {
  login: (data: LoginRequest) => api.post<AuthResponse>('/auth/login', data),
  logout: () => api.post('/auth/logout', {}),
  getMe: () => api.get<User>('/auth/me'),
};

// 입원 관리 API
export interface AdmissionListParams {
  department?: string;
  startDate?: string;
  endDate?: string;
  page?: number;
  limit?: number;
}

export interface SafetyIncidentRequest {
  admissionId: string;
  incidentType: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  description: string;
  occurredAt: string;
}

export interface CdiQueryRequest {
  admissionId: string;
  queryType: string;
  description: string;
  priority?: 'low' | 'medium' | 'high';
}

export interface CsvUploadResponse {
  rows_processed: number;
  message: string;
}

export interface DocumentStats {
  total_documents: number;
  chunk_count: number;
  total_embeddings: number;
  document_count: number;
  status: 'active' | 'inactive' | 'error';
}

export const admissionsApi = {
  list: (params?: AdmissionListParams) => api.get<Admission[]>('/admissions', { params }),
  get: (admissionId: string) => api.get<Admission>(`/admissions/${admissionId}`),
  uploadCsv: (file: File) => api.uploadFile<CsvUploadResponse>('/admissions/upload-csv', file),
  reportSafetyIncident: (data: SafetyIncidentRequest) => api.post('/admissions/safety-incident', data),
  createCdiQuery: (data: CdiQueryRequest) => api.post('/admissions/cdi-query', data),
};

// 예측 API
export const predictionsApi = {
  predictGroup: (data: PredictionRequest) => api.post<GroupPrediction>('/predictions/group', data),
  predictDenialRisk: (data: PredictionRequest) => api.post<DenialRisk>('/predictions/denial-risk', data),
  predictComprehensive: (data: PredictionRequest, admissionId?: string) =>
    api.post<PredictionResponse>(`/predictions/comprehensive?admission_id=${admissionId || ''}`, data),
  batchPredict: (requests: PredictionRequest[]) => api.post('/predictions/batch', requests),
  checkCompliance: (data: PredictionRequest) => api.post<ComplianceReport>('/predictions/compliance', data),
};

// 문서 API
export const documentsApi = {
  upload: (file: File, docType?: string) => api.uploadFile('/documents/upload', file, { doc_type: docType }),
  query: (question: string, contextType?: string, useLlm?: boolean) =>
    api.post('/documents/query', { question, context_type: contextType, use_llm: useLlm }),
  getStats: () => api.get<DocumentStats>('/documents/stats'),
  delete: (documentId: number) => api.delete(`/documents/${documentId}`),
};

// 대시보드 API
export const dashboardApi = {
  getSummary: (department?: string, days?: number) =>
    api.get<DashboardMetrics>('/dashboard/summary', { params: { department, days } }),
  getCmiMetrics: (department?: string, startDate?: string, endDate?: string) =>
    api.get('/dashboard/cmi', { params: { department, start_date: startDate, end_date: endDate } }),
  getDenialAnalytics: (startDate?: string, endDate?: string) =>
    api.get('/dashboard/denials', { params: { start_date: startDate, end_date: endDate } }),
  getGroupDistribution: (department?: string, days?: number) =>
    api.get<GroupDistribution>('/dashboard/group-distribution', { params: { department, days } }),
  getTopDiagnoses: (limit?: number, days?: number) =>
    api.get<TopDiagnoses>('/dashboard/top-diagnoses', { params: { limit, days } }),
  getPerformanceMetrics: (days?: number) =>
    api.get('/dashboard/performance-metrics', { params: { days } }),
};
