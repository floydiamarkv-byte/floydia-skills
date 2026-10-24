# FloydIA Web Production Standards & Lessons Learned (Suite V11.0)

> **Autoridad:** Agente Director / Suite FloydIA  
> **Alcance:** Proyectos web institucionales, landings B2B, portales de catálogo y tiendas para clientes.  
> **Origen:** Lecciones consolidadas del despliegue en producción de Evergreen Technologies C.A. (evergreenvzla.com).

---

## 💎 1. Checklist Inmutable de los 16 Requerimientos de Producción

Toda web construida bajo la Suite FloydIA DEBE cumplir y certificar estos 16 estándares antes del cierre de entrega:

### 1. Página 404 Personalizada (404.html)
- No depender de las páginas 404 genéricas del servidor.
- Debe mantener el header institucional, estética dark/light corporativa, buscador o accesos rápidos a las categorías principales y un botón de contingencia directo a WhatsApp/Soporte.

### 2. Meta Title Único por Página
- Cada página HTML debe poseer un <title> descriptivo, no genérico.
- Estructura canónica: [Nombre Producto / Sección] • [Propuesta de Valor] | [Marca Institucional].

### 3. Meta Description Adaptada
- Longitud entre 120 y 160 caracteres.
- Redacción técnica/comercial sin relleno vacío, conteniendo palabras clave semánticas, garantías y diferenciadores clave.

### 4. Favicon y Apple Touch Icon
- Uso de SVG canónico escalable (<link rel="icon" type="image/svg+xml" href="...">).
- Inclusión de <link rel="apple-touch-icon" href="..."> para dispositivos móviles.

### 5. robots.txt Canónico
- Archivo robots.txt en la raíz que permita rastreo limpio (User-agent: *, Allow: /).
- Declaración explícita del sitemap: Sitemap: https://<dominio>/sitemap.xml.

### 6. sitemap.xml Canónico
- Archivo XML con todas las URLs públicas, atributos <loc>, <lastmod>, <changefreq> y <priority>.

### 7. Open Graph y Twitter Cards Completos
- Inyección en el <head> de:
  - og:type, og:site_name, og:locale
  - og:title, og:description, og:url
  - og:image (resolución mínima 1200x630 o 1600x900), og:image:width, og:image:height, og:image:alt
  - twitter:card="summary_large_image", twitter:title, twitter:description, twitter:image.

### 8. Alt Text en 100% de las Imágenes
- Cada etiqueta <img> debe contar con un atributo alt contextual y descriptivo para accesibilidad (WCAG 2.2 AA) y SEO visual.

### 9. Responsive Mobile-First & Touch Targets
- Viewport configurado con width=device-width, initial-scale=1.0.
- Menú hamburguesa accesible con botón de cierre explícito y cierre al tocar fuera (backdrop click).
- Targets táctiles mínimos de >= 48px para botones, enlaces y campos de formulario.
- Respeto del env(safe-area-inset) en iOS y Android.

### 10. Estados de Carga y Anti-Doble Envío (Loading Spinners)
- Los formularios (RFQ, contacto, checkout) deben mostrar spinner animado (.spinner-btn) y bloquear el botón (disabled) durante la petición de red para prevenir submits duplicados.

### 11. Mensajería de Error Accesible y Canal de Contingencia
- Notificaciones de error legibles en pantalla.
- Fallback automático: ante fallo de red o backend, ofrecer un botón que transfiera los datos del formulario directamente a un chat de WhatsApp pre-rellenado con la solicitud.

### 12. Términos, Condiciones y Garantías Legales (terminos-y-condiciones.html)
- Página formal de marco legal que especifique:
  - Tiempo y cobertura de la garantía escrita.
  - Régimen de facturación legal (e.g. SENIAT a tasa oficial BCV en Venezuela).
  - Tiempos de despacho, almacén físico y políticas de inspección o reemplazo.

### 13. Banner de Cookies B2B con Persistencia
- Banner no invasivo (#cookie-consent-banner) con persistencia de consentimiento en localStorage.
- Si el usuario ya aceptó, no vuelve a mostrarse en cargas sucesivas.

### 14. Telemetría y Analytics (dataLayer)
- Pipeline de eventos listo en window.dataLayer = window.dataLayer || [];.
- Disparo de eventos clave: rfq_submit, whatsapp_click, cookie_consent_accept.

### 15. Formas Reales de Contacto
- Datos de contacto operativos y clicables: enlace telefónico tel:, WhatsApp B2B https://wa.me/, correo electrónico mailto:, formulario RFQ interactivo y ubicación del almacén físico.

### 16. Optimización Integral de Assets (WebP + SVG)
- 100% de fotografías en formato .webp optimizadas (<300 KB c/u).
- Iconos y logotipos en .svg.
- Eliminación estricta de PNGs/JPGs pesados sin procesar para mantener el peso total del sitio por debajo de 5-6 MB.

---

## 🛠️ 2. Lecciones Críticas de Frontend y Despliegue

1. **Balance de Llaves CSS Estricto**:
   - Un error de sintaxis como una llave sin cerrar (}) en CSS invalida silenciosamente todas las reglas y media queries que le siguen. Siempre validar con script de balance de llaves antes de desplegar.
2. **Degradados y Paleta Semántica**:
   - Fondos de secciones intermedias deben usar matices oscuros profundos (#06130d a #020805) en vez de turquesas chillones para mantener la elegancia industrial.
3. **Pill Badges Técnicos**:
   - Evitar recuadros masivos o corchetes toscos. Usar border-radius: 999px, fondo sutil translúcido, fuente monoespaciada o sans clara y espaciado proporcional.
4. **Despliegue y Purga de Caché en Producción**:
   - Al actualizar archivos estáticos en entornos con WordPress/Apache/Nginx, purgar siempre las carpetas de caché (wp-content/cache/) y verificar la directiva DirectoryIndex en .htaccess.
5. **Estabilidad de Automatizaciones Playwright**:
   - En Linux headless, siempre lanzar Chromium con argumentos --no-sandbox, --disable-setuid-sandbox, --disable-dev-shm-usage, --disable-gpu y timeouts explícitos para garantizar ejecuciones de <5 segundos.
