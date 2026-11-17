import api from './api';
import { UserProfile } from '../types';

export interface RegisterPayload {
  username: string;
  email: string;
  password: string;
  full_name?: string;
}

export interface LoginPayload {
  username_or_email: string;
  password: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: UserProfile;
}

export interface ProfileUpdatePayload {
  full_name?: string;
  email?: string;
  current_password?: string;
  new_password?: string;
}

export const authApi = {
  register: async (payload: RegisterPayload): Promise<AuthResponse> => {
    const response = await api.post<AuthResponse>('/auth/register', payload);
    return response.data;
  },

  login: async (payload: LoginPayload): Promise<AuthResponse> => {
    const response = await api.post<AuthResponse>('/auth/login', payload);
    return response.data;
  },

  getMe: async (): Promise<UserProfile> => {
    const response = await api.get<UserProfile>('/auth/me');
    return response.data;
  },

  updateProfile: async (payload: ProfileUpdatePayload): Promise<UserProfile> => {
    const response = await api.put<UserProfile>('/auth/profile', payload);
    return response.data;
  },
};
