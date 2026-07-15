// 前端类型定义
export interface TripRequest {
  destination: string
  start_date: string
  end_date: string
  travelers: number
  budget?: number
  preferences?: string
  pace?: string
  hotel_level?: string
  special_notes?: string
}

export interface Location {
  address?: string
  latitude?: number
  longitude?: number
  poi_id?: string
}

export interface SpotItem {
  name: string
  start_time?: string
  end_time?: string
  description?: string
  estimated_cost?: number
  location?: Location
  image_url?: string
}

export interface MealItem {
  type: string
  name: string
  description?: string
  estimated_cost?: number
}

export interface BudgetBreakdown {
  transport: number
  hotel: number
  meals: number
  tickets: number
  other: number
  total: number
}

export interface HotelItem {
  name: string
  level?: string
  estimated_cost?: number
  location?: Location
  notes?: string
}

export interface DayPlan {
  day_index: number
  date?: string
  theme?: string
  spots: SpotItem[]
  meals: MealItem[]
  hotel?: HotelItem | null
  notes?: string
}

export interface Itinerary {
  trip_id: string
  destination: string
  summary: string
  days: DayPlan[]
  estimated_budget: number
  budget_breakdown: BudgetBreakdown
  tips: string[]
  source_notes: string[]
}

export interface TripGenerateResponse {
  trip_id: string
  itinerary: Itinerary
}

export interface TripSummaryItem {
  trip_id: string
  destination: string
  summary: string
  created_at: string
  updated_at: string
}

export interface WeatherForecast {
  date: string
  day_weather: string
  night_weather: string
  day_temp: number
  night_temp: number
  wind_direction: string
}

export interface WeatherResponse {
  city: string
  forecasts: WeatherForecast[]
}
