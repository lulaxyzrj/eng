import { Injectable, NgZone } from '@angular/core';
import { MessageService } from 'primeng/api';

@Injectable({
  providedIn: 'root'
})
export class ToastService {

  constructor(
    private messageService: MessageService,
    private zone: NgZone) { }

  showSuccess(message: string, key?: string): void {
    // Had an issue with the snackbar being ran outside of angular's zone.
    this.zone.run(() => {
      this.messageService.add({ severity: 'success', detail: message, key: key });
    });
  }

  showWarning(message: string, key?: string): void {
    // Had an issue with the snackbar being ran outside of angular's zone.
    this.zone.run(() => {
      this.messageService.add({ severity: 'warn', detail: message, key: key });
    });
  }

  showError(message: string, key?: string): void {
    this.zone.run(() => {
      // The second parameter is the text in the button.
      // In the third, we send in the css class for the snack bar.
      this.messageService.add({ severity: 'error', detail: message, life: 10000, key: key });
    });
  }
}
