import { Component } from '@angular/core';
import { TranslateService } from '@ngx-translate/core';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss']
})
export class AppComponent {
  title = 'engdb-dev-test2';

  constructor(private translate: TranslateService) {
    this.translate.setDefaultLang('pt');
  }

  getTaskMenuLabel() {
    return this.translate.instant('task.titlePage')
  }
}
