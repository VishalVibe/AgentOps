import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterOutlet } from '@angular/router';
import { ApiService, QueueItem } from './api.service';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterOutlet],
  templateUrl: './app.html',
  styleUrl: './app.css'
})
export class AppComponent implements OnInit {
  title = 'AgentOps Review Dashboard';
  queue: QueueItem[] = [];
  selectedTask: QueueItem | null = null;
  modifiedResult: string = '';

  constructor(private apiService: ApiService) {}

  ngOnInit() {
    this.loadQueue();
  }

  loadQueue() {
    this.apiService.getQueue().subscribe({
      next: (res) => {
        this.queue = res.queue;
      },
      error: (err) => console.error(err)
    });
  }

  selectTask(task: QueueItem) {
    this.selectedTask = task;
    // Find the current subtask result
    const currentSubtask = task.plan.subtasks.find((st: any) => st.id === task.current_subtask_id);
    this.modifiedResult = currentSubtask ? currentSubtask.result : '';
  }

  resolve(action: 'approve' | 'modify' | 'take_over') {
    if (!this.selectedTask) return;

    this.apiService.resolveEscalation(this.selectedTask.task_id, {
      action,
      modifiedResult: this.modifiedResult
    }).subscribe({
      next: () => {
        this.selectedTask = null;
        this.loadQueue();
      },
      error: (err) => console.error(err)
    });
  }
}
