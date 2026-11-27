import axios from 'axios'

const client = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000',
})

export async function predictRisk(patientData) {
  const response = await client.post('/predict', patientData)
  return response.data
}

export async function getRecommendations(patientData) {
  const response = await client.post('/recommendations', patientData)
  return response.data
}

export async function searchFoods(query) {
  const response = await client.get('/external/foods', { params: { query, limit: 1 } })
  return response.data.results
}

export async function searchDrugLabels(query) {
  const response = await client.get('/external/drug-labels', { params: { query, limit: 1 } })
  return response.data.results
}

export async function searchPackagedFoods(query) {
  const response = await client.get('/external/packaged-foods', { params: { query, limit: 1 } })
  return response.data.results
}

export async function findNearbyCare(latitude, longitude) {
  const response = await client.get('/external/nearby-care', { params: { latitude, longitude } })
  return response.data.results
}

export async function getDatasetPreview(dataset) {
  const response = await client.get(`/datasets/${dataset}`)
  return response.data
}

export async function getPhase1DatasetPreview(dataset) {
  const response = await client.get(`/phase1/datasets/${dataset}`)
  return response.data
}

export async function askPhase2Question(question) {
  const response = await client.post('/phase2/questions', { question })
  return response.data
}
