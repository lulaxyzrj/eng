import { Component } from '@angular/core';
import { FieldWrapper } from '@ngx-formly/core';

@Component({
    selector: 'grm-horizontal-wrapper',
    template: `
    <div class="form-group" [class.error]="showError">
      <label [attr.for]="id" class="col-md-2 col-form-label" *ngIf="to.label">
        {{ to.label }}
        <span *ngIf="to.required" class="ng-star-inserted">*</span>
      </label>
      <div class="col-md-10">
        <ng-template #fieldComponent></ng-template>
      </div>
    </div>
  `,
})
export class HorizontalWrapperComponent extends FieldWrapper {
}
