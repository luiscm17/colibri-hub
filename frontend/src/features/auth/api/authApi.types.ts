export type NextStep = 'change_password' | 'load_access'

export interface AuthMeResponse {
  account_id: string
  email: string
  display_name: string
  status: string
  next_step: NextStep
}

export interface PasswordChangeRequest {
  current_password: string
  new_password: string
}

export interface AuthenticationAccountResponse {
  account_id: string
  email: string
  display_name: string
  user_code: string
  status: string
  version: number
}

export interface ProvisionAccountRequest {
  email: string
  provisional_password: string
  user_code: string
  display_name: string
  role_codes: string[]
  reason: string
}

export type ProvisionAccountResponse = AuthenticationAccountResponse

export interface ResetPasswordRequest {
  provisional_password: string
  reason: string
  expected_version: number
}

export interface DisableAccountRequest {
  reason: string
  expected_version: number
}

export interface EnableAccountRequest {
  provisional_password: string
  reason: string
  expected_version: number
}
