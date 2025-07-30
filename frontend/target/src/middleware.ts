import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  const token = request.cookies.get('token')?.value;
  const { pathname } = request.nextUrl;

  // Se não há token e o usuário tenta acessar o dashboard
  if (!token && pathname.startsWith('/dashboard')) {
    const loginUrl = new URL('/login', request.url);
    return NextResponse.redirect(loginUrl);
  }

  // Se há um token e o usuário tenta acessar login ou registro
  if (token && (pathname === '/login' || pathname.startsWith('/users/register'))) {
    const dashboardUrl = new URL('/dashboard', request.url);
    return NextResponse.redirect(dashboardUrl);
  }

  return NextResponse.next();
}

// Define os caminhos onde o middleware será executado
export const config = {
  matcher: ['/dashboard/:path*', '/login', '/users/register'],
};
