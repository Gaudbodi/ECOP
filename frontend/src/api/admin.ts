import { apiFetch } from './client'
import type { NewUserPayload, Stakeholder, User } from './types'

export interface UsersListResponse {
  users: User[]
}

export interface StakeholdersResponse {
  stakeholders: Stakeholder[]
}

export interface CreateUserResponse {
  status: 'created'
  user: User
  warning?: string
}

export function fetchAdminUsers(): Promise<UsersListResponse> {
  return apiFetch<UsersListResponse>('/api/v1/admin/users')
}

export function fetchStakeholders(): Promise<StakeholdersResponse> {
  return apiFetch<StakeholdersResponse>('/api/v1/admin/stakeholders')
}

export function createAdminUser(payload: NewUserPayload): Promise<CreateUserResponse> {
  return apiFetch<CreateUserResponse>('/api/v1/admin/users', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}
