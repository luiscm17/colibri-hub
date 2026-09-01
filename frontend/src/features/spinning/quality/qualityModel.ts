import type { QualityMeasurement, QualityProfile } from '../integration/contracts'

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

export type SampleQualityRow = QualityMeasurement & Readonly<{ value: string }>

export function sampleQualityRows(measurements: readonly QualityMeasurement[], values: Readonly<Record<string, string>>): readonly SampleQualityRow[] {
  return measurements.map(measurement => ({ ...measurement, value: values[measurement.id] ?? '' }))
}

export function sampleMeasurementValidationError(row: Pick<SampleQualityRow, 'required' | 'validation' | 'value'>): string | undefined {
  const value = row.value.trim()
  if (!value) return row.required ? 'La medición es obligatoria.' : undefined
  if (row.validation === 'decimal' && !/^-?(?:0|[1-9]\d*)(?:[.,]\d+)?$/.test(value)) return 'Ingrese un valor decimal válido.'
  if (row.validation === 'integer' && !/^-?(?:0|[1-9]\d*)$/.test(value)) return 'Ingrese un número entero válido.'
  return undefined
}
