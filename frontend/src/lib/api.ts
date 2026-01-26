import type {
  Dataset,
  Case,
  RunSummary,
  Run,
  Baseline,
  Settings,
  CreateDatasetRequest,
  CreateCaseRequest,
  UpdateCaseRequest,
} from '@/types'

const API_BASE = '/api'

async function fetchJSON<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Request failed' }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }

  return response.json()
}

// Datasets
export async function listDatasets(): Promise<Dataset[]> {
  return fetchJSON(`${API_BASE}/datasets`)
}

export async function getDataset(identifier: string): Promise<Dataset> {
  return fetchJSON(`${API_BASE}/datasets/${encodeURIComponent(identifier)}`)
}

export async function createDataset(data: CreateDatasetRequest): Promise<Dataset> {
  return fetchJSON(`${API_BASE}/datasets`, {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function updateDataset(identifier: string, data: Partial<CreateDatasetRequest>): Promise<Dataset> {
  return fetchJSON(`${API_BASE}/datasets/${encodeURIComponent(identifier)}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  })
}

export async function deleteDataset(identifier: string): Promise<void> {
  await fetchJSON(`${API_BASE}/datasets/${encodeURIComponent(identifier)}`, {
    method: 'DELETE',
  })
}

// Cases
export async function listCases(datasetId?: string): Promise<Case[]> {
  const params = datasetId ? `?dataset_id=${encodeURIComponent(datasetId)}` : ''
  return fetchJSON(`${API_BASE}/cases${params}`)
}

export async function getCase(datasetId: string, caseId: string): Promise<Case> {
  return fetchJSON(`${API_BASE}/cases/${encodeURIComponent(datasetId)}/${encodeURIComponent(caseId)}`)
}

export async function createCase(data: CreateCaseRequest): Promise<Case> {
  return fetchJSON(`${API_BASE}/cases`, {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function updateCase(datasetId: string, caseId: string, data: UpdateCaseRequest): Promise<Case> {
  return fetchJSON(`${API_BASE}/cases/${encodeURIComponent(datasetId)}/${encodeURIComponent(caseId)}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  })
}

export async function deleteCase(datasetId: string, caseId: string): Promise<void> {
  await fetchJSON(`${API_BASE}/cases/${encodeURIComponent(datasetId)}/${encodeURIComponent(caseId)}`, {
    method: 'DELETE',
  })
}

// Runs
export async function listRuns(datasetId?: string): Promise<RunSummary[]> {
  const params = datasetId ? `?dataset_id=${encodeURIComponent(datasetId)}` : ''
  return fetchJSON(`${API_BASE}/runs${params}`)
}

export async function getRun(datasetId: string, filename: string): Promise<Run> {
  return fetchJSON(`${API_BASE}/runs/${encodeURIComponent(datasetId)}/${encodeURIComponent(filename)}`)
}

export async function deleteRun(datasetId: string, filename: string): Promise<void> {
  await fetchJSON(`${API_BASE}/runs/${encodeURIComponent(datasetId)}/${encodeURIComponent(filename)}`, {
    method: 'DELETE',
  })
}

// Baselines
export async function listBaselines(): Promise<Baseline[]> {
  return fetchJSON(`${API_BASE}/baselines`)
}

export async function getBaseline(datasetId: string): Promise<Baseline> {
  return fetchJSON(`${API_BASE}/baselines/${encodeURIComponent(datasetId)}`)
}

// Settings
export async function getSettings(): Promise<Settings> {
  return fetchJSON(`${API_BASE}/settings`)
}

export async function updateSettings(settings: Partial<Settings>): Promise<Settings> {
  return fetchJSON(`${API_BASE}/settings`, {
    method: 'PUT',
    body: JSON.stringify(settings),
  })
}

// Generate dataset from description
export async function generateDataset(productDescription: string): Promise<Dataset> {
  return fetchJSON(`${API_BASE}/datasets/generate`, {
    method: 'POST',
    body: JSON.stringify({ product_description: productDescription }),
  })
}

