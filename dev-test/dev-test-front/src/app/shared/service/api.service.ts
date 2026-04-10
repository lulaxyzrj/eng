import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from 'src/environments/environment'; // Importando o ambiente

@Injectable({
  providedIn: 'root'
})
export class ApiService {

  private apiUrl = environment.backendUrl;

  constructor(private http: HttpClient) {}

  inactivate(data: any) {
    return this.http.put(`${this.apiUrl}/tasks/setInactive`, data);
  }

  reactivate(data: any) {
    return this.http.put(`${this.apiUrl}/tasks/setActive`, data);
  }
}