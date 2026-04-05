import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-auth-screen',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './auth-screen.component.html',
  styleUrls: ['./auth-screen.component.scss'],
})
export class AuthScreenComponent {
  @Input() errorMessage = '';
  @Output() connect = new EventEmitter<void>();
}
