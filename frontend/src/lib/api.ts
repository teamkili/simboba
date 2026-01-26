import type { Dataset, Run, RunSummary, Settings, Case, MessageInput } from '@/types'

const BASE_URL = '/api'

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  })

  if (!response.ok) {
    const error = await response.text()
    throw new Error(error || `Request failed: ${response.status}`)
  }

  return response.json()
}

// Datasets
export async function listDatasets(): Promise<Dataset[]> {
  return request<Dataset[]>('/datasets')
}

export async function getDataset(identifier: string): Promise<Dataset> {
  return request<Dataset>(`/datasets/${identifier}`)
}

export async function createDataset(data: { name: string; description?: string }): Promise<Dataset> {
  return request<Dataset>('/datasets', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function updateDataset(identifier: string, data: Partial<Dataset>): Promise<Dataset> {
  return request<Dataset>(`/datasets/${identifier}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  })
}

export async function deleteDataset(identifier: string): Promise<void> {
  await request<void>(`/datasets/${identifier}`, { method: 'DELETE' })
}

export async function generateDataset(description: string): Promise<Dataset> {
  return request<Dataset>('/datasets/generate', {
    method: 'POST',
    body: JSON.stringify({ description }),
  })
}

// Cases
export async function listCases(datasetId: string): Promise<Case[]> {
  return request<Case[]>(`/cases?dataset_id=${encodeURIComponent(datasetId)}`)
}

export async function createCase(data: {
  dataset_name: string
  name?: string
  inputs: MessageInput[]
  expected_outcome: string
  expected_metadata?: Record<string, unknown>
}): Promise<Case> {
  return request<Case>('/cases', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function updateCase(
  datasetId: string,
  caseId: string,
  data: Partial<Case>
): Promise<Case> {
  return request<Case>(`/cases/${datasetId}/${caseId}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  })
}

export async function deleteCase(datasetId: string, caseId: string): Promise<void> {
  await request<void>(`/cases/${datasetId}/${caseId}`, { method: 'DELETE' })
}

// Runs
export async function listRuns(): Promise<RunSummary[]> {
  return request<RunSummary[]>('/runs')
}

export async function getRun(datasetId: string, filename: string): Promise<Run> {
  return request<Run>(`/runs/${datasetId}/${filename}`)
}

export async function deleteRun(datasetId: string, filename: string): Promise<void> {
  await request<void>(`/runs/${datasetId}/${filename}`, { method: 'DELETE' })
}

// Settings
export async function getSettings(): Promise<Settings> {
  return request<Settings>('/settings')
}

export async function updateSettings(settings: Partial<Settings>): Promise<Settings> {
  return request<Settings>('/settings', {
    method: 'PUT',
    body: JSON.stringify(settings),
  })
}

// Files
export async function uploadFile(file: File): Promise<{ filename: string }> {
  const formData = new FormData()
  formData.append('file', file)

  const response = await fetch(`${BASE_URL}/files/upload`, {
    method: 'POST',
    body: formData,
  })

  if (!response.ok) {
    throw new Error('File upload failed')
  }

  return response.json()
}
