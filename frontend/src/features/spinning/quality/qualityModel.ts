import type { QualityProfile, QualitySampleRecord } from '../integration/contracts'

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

export function updateSampleRecord(records: readonly QualitySampleRecord[], recordId: string, sampleIndex: number, value: string): readonly QualitySampleRecord[] {
  return records.map(record => record.id !== recordId ? record : {
    ...record,
    samples: Array.from({ length: Math.max(record.samples.length, sampleIndex + 1) }, (_, index) => index === sampleIndex ? value : record.samples[index] ?? ''),
  })
}
