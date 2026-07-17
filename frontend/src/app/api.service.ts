import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface QueueItem {
  task_id: string;
  original_task: string;
  plan: any;
  current_subtask_id: string;
}

export interface ResolveRequest {
  action: 'approve' | 'modify' | 'take_over';
  modified_result?: string;
}

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private baseUrl = '/api';

  constructor(private http: HttpClient) {}

  getQueue(): Observable<{queue: QueueItem[]}> {
    return this.http.get<{queue: QueueItem[]}>(`${this.baseUrl}/queue`);
  }

  resolveEscalation(taskId: string, req: ResolveRequest): Observable<any> {
    return this.http.post(`${this.baseUrl}/queue/${taskId}/resolve`, req);
  }
}
