import axios from "axios";
import type {
  Ticket,
  CreateTicketData,
  UpdateTicketData,
  TicketListResponse,
} from "@/types/ticket";
import type { Tag, CreateTagData, TagListResponse } from "@/types/tag";

const API_BASE_URL = "/api/v1";

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Ticket API
export const ticketApi = {
  list: async (params?: {
    status?: string;
    tag_ids?: string;
    search?: string;
    skip?: number;
    limit?: number;
  }): Promise<TicketListResponse> => {
    const { data } = await api.get("/tickets", { params });
    return data;
  },

  get: async (id: number): Promise<Ticket> => {
    const { data } = await api.get(`/tickets/${id}`);
    return data;
  },

  create: async (ticket: CreateTicketData): Promise<Ticket> => {
    const { data } = await api.post("/tickets", ticket);
    return data;
  },

  update: async (id: number, ticket: UpdateTicketData): Promise<Ticket> => {
    const { data } = await api.put(`/tickets/${id}`, ticket);
    return data;
  },

  delete: async (id: number): Promise<void> => {
    await api.delete(`/tickets/${id}`);
  },

  complete: async (id: number): Promise<Ticket> => {
    const { data } = await api.patch(`/tickets/${id}/complete`);
    return data;
  },

  uncomplete: async (id: number): Promise<Ticket> => {
    const { data } = await api.patch(`/tickets/${id}/uncomplete`);
    return data;
  },

  addTags: async (id: number, tagIds: number[]): Promise<Ticket> => {
    const { data } = await api.post(`/tickets/${id}/tags`, tagIds);
    return data;
  },

  removeTag: async (id: number, tagId: number): Promise<void> => {
    await api.delete(`/tickets/${id}/tags/${tagId}`);
  },
};

// Tag API
export const tagApi = {
  list: async (): Promise<TagListResponse> => {
    const { data } = await api.get("/tags");
    return data;
  },

  get: async (id: number): Promise<Tag> => {
    const { data } = await api.get(`/tags/${id}`);
    return data;
  },

  create: async (tag: CreateTagData): Promise<Tag> => {
    const { data } = await api.post("/tags", tag);
    return data;
  },

  delete: async (id: number): Promise<void> => {
    await api.delete(`/tags/${id}`);
  },
};
