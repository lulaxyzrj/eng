import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { GRMFormlyModule } from './formly/formly.module';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { DragDropModule } from '@angular/cdk/drag-drop';
import { CommonPrimengModule } from './ui-elements/common-primeng.module';

@NgModule({
  imports: [CommonPrimengModule, DragDropModule, GRMFormlyModule, BrowserAnimationsModule],
  exports: [CommonPrimengModule, DragDropModule, CommonModule, GRMFormlyModule, BrowserAnimationsModule]
})
export class SharedLibsModule {
  static forRoot() {
    return {
      ngModule: SharedLibsModule
    };
  }
}
