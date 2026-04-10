import { NgModule } from '@angular/core';
import { EffectsModule } from '@ngrx/effects';
import { StoreModule } from '@ngrx/store';
import { StoreDevtoolsModule } from '@ngrx/store-devtools';
import { DefaultDataServiceConfig, EntityDataModule } from '@ngrx/data';
import { defaultDataServiceConfig } from './config';
import { entityConfig } from './entity-metadata';
import { environment } from 'src/environments/environment';

@NgModule({
    imports: [
        StoreModule.forRoot({}, {
            runtimeChecks: {
            }
        }),
        EffectsModule.forRoot([]),
        environment.production ? [] : StoreDevtoolsModule.instrument({
            maxAge: 25
        }),
        EntityDataModule.forRoot(entityConfig)
    ],
    providers: [
        { provide: DefaultDataServiceConfig, useValue: defaultDataServiceConfig }
    ]
})
export class AppStoreModule {
    constructor() {}
}
