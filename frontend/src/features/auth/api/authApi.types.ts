export type NextStep = 'change_password' | 'load_access'

export interface AuthMeResponse {
  account_id: string
  email: string
  display_name: string
  initials: string
  version: number
  next_step: NextStep
}

export interface PasswordChangeRequest {
  current_password: string
  new_password: string
}

export interface PasswordChangeResponse {
  message: string
}
