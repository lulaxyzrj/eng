import { BrowserModule } from '@angular/platform-browser';
import { LOCALE_ID, NgModule } from '@angular/core';
import localePTBR from '@angular/common/locales/pt';
import { TranslateHttpLoader } from '@ngx-translate/http-loader';

import { AppComponent } from './app.component';
import { TableModule, ToastModule } from 'primeng';
import { TaskModule } from './features/task/task.module';
import { RouterModule, Routes } from '@angular/router';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { FormlyModule } from '@ngx-formly/core';
import { HttpClient, HttpClientModule } from '@angular/common/http';
import { TranslateLoader, TranslateModule } from '@ngx-translate/core';
import { registerLocaleData } from '@angular/common';
import { SharedModule } from './shared/shared.module';
import { HomeComponent } from './home/home.component';
import { AppRoutingModule } from './app-routing.module';
import { EntityActionFactory, EntityCollectionServiceElementsFactory, EntityDataModule, EntityDataService, EntityDispatcherDefaultOptions, EntityDispatcherFactory } from '@ngrx/data';
import { entityConfig } from './store/entity-metadata';
import { Actions, EffectSources } from '@ngrx/effects';
import { AppStoreModule } from './store/store.module';

registerLocaleData(localePTBR);

export function HttpLoaderFactory(http: HttpClient) {
  return new TranslateHttpLoader(http, './assets/i18n/', '.json');
}

@NgModule({
  declarations: [
    AppComponent, HomeComponent
  ],
  imports: [
    BrowserModule,
    TableModule,
    ToastModule,
    FormsModule,
    FormlyModule,
    ReactiveFormsModule,
    SharedModule,
    TaskModule,
    HttpClientModule,
    AppRoutingModule,
    AppStoreModule,
    EntityDataModule.forRoot(entityConfig),
    TranslateModule.forRoot({
      loader: {
        provide: TranslateLoader,
        useFactory: HttpLoaderFactory,
        deps: [HttpClient]
      }
    })
  ],
  exports: [RouterModule, HomeComponent],
  providers: [
    {provide: LOCALE_ID, useValue: 'pt-BR'},
    EntityCollectionServiceElementsFactory,
    EntityDataService,
    EntityDispatcherFactory,
    EntityActionFactory,
    EntityDispatcherDefaultOptions,
    Actions,
    EffectSources
  ],
  bootstrap: [AppComponent]
})
export class AppModule { }
