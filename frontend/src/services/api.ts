// API 服务封装
import axios from "axios"
import type {
  TripRequest, TripGenerateResponse,
  TripSummaryItem, Itinerary, WeatherResponse
} from "../types"

const api = axios.create({
  baseURL: "/api",
  timeout: 120000,
})

export async function generateTrip(payload: TripRequest): Promise<TripGenerateResponse> {
  const { data } = await api.post("/trip/generate", payload)
  return data
}

export async function saveTrip(itinerary: Itinerary): Promise<any> {
  const { data } = await api.post("/trip/save", {
    trip_id: itinerary.trip_id,
    destination: itinerary.destination,
    summary: itinerary.summary,
    itinerary_json: JSON.stringify(itinerary),
  })
  return data
}

export async function listTrips(): Promise<TripSummaryItem[]> {
  const { data } = await api.get("/trip")
  return data.trips || []
}

export async function getTripDetail(tripId: string): Promise<Itinerary> {
  const { data } = await api.get(`/trip/${tripId}`)
  return data
}

export async function deleteTrip(tripId: string): Promise<any> {
  const { data } = await api.delete(`/trip/${tripId}`)
  return data
}

export async function editTripDay(tripId: string, dayIndex: number, instruction: string): Promise<any> {
  const { data } = await api.post("/trip/edit", { trip_id: tripId, day_index: dayIndex, instruction })
  return data
}

export async function fetchWeather(city: string): Promise<WeatherResponse> {
  const { data } = await api.get("/weather/forecast", { params: { city } })
  return data
}

export function getMarkdownUrl(tripId: string): string {
  return `/export/${tripId}/markdown`
}

export function getPdfUrl(tripId: string): string {
  return `/export/${tripId}/pdf`
}
