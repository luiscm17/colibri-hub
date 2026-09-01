import type { QualityProfile } from '../integration/contracts'

export type QualityDraft = Readonly<{
  profileId: string
  values: Readonly<Record<string, string>>
}>

export function createQualityDraft(): QualityDraft {
  return { profileId: '', values: {} }
}

export function selectQualityProfile(draft: QualityDraft, profileId: string): QualityDraft {
  return { ...draft, profileId }
}

export function updateQualityDraft(draft: QualityDraft, fieldId: string, value: string): QualityDraft {
  return { ...draft, values: { ...draft.values, [fieldId]: value } }
}

export function selectedQualityProfile(profiles: readonly QualityProfile[], draft: QualityDraft): QualityProfile | undefined {
  return profiles.find(profile => profile.id === draft.profileId)
}
