---
document_type: research
status: active
implementation: not-applicable
scope: global/infrastructure
authority: evidence
owner: platform
last_reviewed: 2026-07-27
---

# Presupuesto de Infraestructura — Colibri Hub

> **Fecha:** Junio 2026
> **Propósito:** Estimar costos mensuales y anuales de infraestructura para el sistema Colibri Hub en producción, considerando el stack definido y alternativas viables.

---

## 1. Stack Tecnológico (decidido)

| Capa | Tecnología | Proveedor |
|---|---|---|
| Frontend | React 18 + Vite + TypeScript | Vercel |
| Backend | FastAPI + SQLAlchemy 2.0 + Alembic | Railway |
| Base de datos | PostgreSQL 15 | Supabase |
| Autenticación | Supabase Auth (JWT) | Supabase |
| DNS / CDN | Cloudflare | Cloudflare (free) |
| Email transaccional | Resend / SendGrid | A definir |
| Dominio | `.com` | Cloudflare / Porkbun |

---

## 2. Escenario Mínimo — Startup / Producción Temprana

Para los primeros meses con ~5-10 usuarios concurrentes (operarios de planta), volúmenes bajos de datos.

### Opción A: PaaS (recomendado — mínimo setup)

| Servicio | Plan | Costo/mes | Notas |
|---|---|---|---|
| **Supabase** | Pro | **$25** | 8 GB DB, 250 GB egress, 100K MAU. No hace falta más para el volumen inicial. Auth incluido. |
| **Railway** | Hobby | **$5** | Backend FastAPI. $5 de crédito incluido. 1 vCPU / 0.5 GB RAM alcanza. Si el backend es pequeño, quizás hasta entre en el free trial ($5/mes gratis primeros 30 días). |
| **Vercel** | Hobby | **$0** | Frontend estático (React + Vite). Builds ilimitados. CDN global incluido. |
| **Cloudflare DNS** | Free | **$0** | DNS, CDN, DDoS, SSL incluido. Panel de control unificado. |
| **Resend** | Free → Pro | **$0** → **$20** | 3.000 emails/mes gratis. Si crece, Pro $20/mes por 50.000. |
| **Dominio .com** | — | ~**$1** ($10.44/año) | Cloudflare a costo, ~$10.44/año = $0.87/mes. Porkbun ~$11.08/año. |

> **Total mensual mínimo:** **~$31/mes** (sin Resend Pro) | **~$51/mes** (con Resend Pro)
> **Total primer año:** **~$372** (sin Resend Pro) | **~$612** (con Resend Pro)

### Desglose realista del Railway Hobby

Railway Hobby da $5 de crédito de uso. El backend FastAPI liviano:
- **RAM:** 512 MB constantes → ~$0.00000386/GB/sec × 0.5 GB × 2.592.000 seg/mes = ~$5.00
- **CPU:** Uso bajo (API requests esporádicas) → normalmente menos de $1-2
- **Egress:** Backend devuelve JSON, tráfico mínimo. DB está en Supabase, no en Railway.

Con 1 servicio pequeño y poco tráfico, los $5 de crédito del Hobby cubren el mes. Si se necesita más RAM/CPU, se paga excedente, pero difícil que pase de $10-15/mes en esta etapa.

---

## 3. Opciones Desagregadas por Servicio

### 3.1 Base de datos — Supabase

| Plan | Costo | DB | Egress | MAU | Backups | Ideal para |
|---|---|---|---|---|---|---|
| **Free** | $0 | 500 MB | 5 GB | 50K | No | Desarrollo local / staging |
| **Pro** | $25/mes | 8 GB | 250 GB | 100K | 7 días | Producción temprana |
| **Team** | $75/mes | 8 GB | 250 GB | 100K | 14 días | Producción con SOC2 / compliance |
| **Enterprise** | Custom | Custom | Custom | Custom | Custom | Escala grande |

**Nota:** Custom domain en Supabase cuesta **$10/dominio/mes extra** (add-on). Para producción real con entorno corporativo, considerar si es necesario.

> **Alternativa directa:** Neon (serverless Postgres). Free tier: 1 vCPU, 1 GiB RAM. Pro: $59/mes (2 vCPU, 4 GiB). Más caro que Supabase para el volumen inicial, pero worth considerar si el equipo prefiere Postgres puro sin Supabase Auth.

### 3.2 Backend hosting

| Proveedor | Plan | Costo | RAM/CPU | Ideal para |
|---|---|---|---|---|
| **Railway** | Hobby | $5/mes (crédito) | 0.5 GB / 1 vCPU | Backend FastAPI producción temprana |
| **Railway** | Pro | $20/mes (crédito) | 1 TB RAM max | Producción con más carga |
| **Render** | Starter | $7/mes | 512 MB / shared vCPU | Alternativa a Railway sin sleep |
| **Render** | Pro | $19/mes | 1 GB / 1 vCPU | Producción estable |
| **Fly.io** | — | ~$5-10/mes | 256 MB / shared | Alternativa edge, más barato pero más setup |

**Sobre Render:** Los web services gratis duermen después de inactividad. El plan Starter $7/mes ya no duerme, más estable que el free.

**Sobre Railway Hobby:** Después del trial de 30 días, el plan Hobby cuesta **$5/mes** (mínimo). Te dan $5 de crédito para consumo. Si tu backend gasta menos de $5 (que es el caso esperado), pagas solo $5.

### 3.3 Frontend hosting

| Proveedor | Plan | Costo | Notas |
|---|---|---|---|
| **Vercel** | Hobby | **$0** | Builds ilimitados, CDN global, SSL automático. No hay razón para pagar con React+Vite. |
| **Vercel** | Pro | $20/mes | Equipos, analytics avanzados, preview deployments. Solo si se necesita. |
| **Cloudflare Pages** | Free | **$0** | Alternativa. 500 builds/mes, 100 dominios, ancho de banda ilimitado. Excelente también. |

### 3.4 Dominio

| Registrador | .com Registro | .com Renovación | 5 años total |
|---|---|---|---|
| **Cloudflare** | ~$10.44 | ~$10.44/año | **$52.30** |
| **Porkbun** | ~$8.88 | ~$11.08/año | **$55.40** |
| **Namecheap** | ~$10.98 | ~$18.48/año | **$85.20** |
| **GoDaddy** | ~$11.99 | ~$22.99/año | **$105+** |

> **Recomendación:** Cloudflare o Porkbun. Ambos a costo, sin markup abusivo en renovaciones. Además Cloudflare ya incluye DNS y CDN gratuitos de primer nivel.

### 3.5 DNS / CDN / Seguridad

| Proveedor | Plan | Costo | Beneficios |
|---|---|---|---|
| **Cloudflare** | Free | **$0** | DNS, CDN global (330+ datacenters), DDoS ilimitado, SSL gratis |
| **Cloudflare** | Pro | $20/mes | WAF avanzado, optimización de imágenes, reglas personalizadas |
| **Cloudflare** | Business | $200/mes | SLA 100%, Page Shield, PCI compliance |

> Para Colibri Hub el plan Free de Cloudflare es más que suficiente. DNS rápido, DDoS protection, y SSL son gratuitos y de nivel enterprise. Solo considerar Pro si se necesitan reglas WAF avanzadas.

### 3.6 Email transaccional

| Proveedor | Free tier | Plan pago inicio | Ideal para |
|---|---|---|---|
| **Resend** | 3.000/mes | $20/mes (50K) | API moderna, React Email, mejor DX |
| **Mailgun** | 100/día | $15/mes (10K) | API robusta, EU hosting disponible |
| **SendGrid** | 100/día | $19.95/mes (50K) | Enterprise, maduro, más features |
| **Amazon SES** | Sin free | $0.10/1K emails | Más barato a escala, más setup |
| **Postmark** | 100/mes (trial) | $15/mes (10K) | Mejor deliverability, solo transactional |

> Para Colibri Hub los emails transaccionales son: reset de contraseña, notificaciones, reportes diarios. Con **Resend free** (3.000/mes) se cubre el primer tiempo. Si el volumen crece, **Pro a $20/mes** es la opción más moderna.

---

## 4. Escenario VPS (auto-gestionado)

Si se quiere independencia de PaaS y menor costo mensual, con más responsabilidad operativa.

### Hetzner Cloud (datacenter Alemania/Francia — latencia aceptable desde Argentina)

| Instancia | vCPU | RAM | Storage | Tráfico | Precio/mes |
|---|---|---|---|---|---|
| **CX Gen3** (shared) | 2 | 4 GB | 40 GB NVMe | 20 TB | ~€5.99 |
| **CAX11** (ARM shared) | 2 | 4 GB | 40 GB NVMe | 20 TB | ~€4.99 |
| **CPX22** (shared AMD) | 2 | 4 GB | 80 GB NVMe | 20 TB | ~€8.49 |
| **CCX13** (dedicado) | 2 | 8 GB | 80 GB NVMe | 20 TB | ~€16.49 |

**Setup VPS (todo en un servidor):**

| Componente | Detalle |
|---|---|
| **VPS** | CAX11 o CX Gen3 (~€5-7/mes) |
| **Sistema** | Docker Compose con: Postgres 15, FastAPI (uvicorn), Nginx reverse proxy |
| **Instalación** | ~2-4 horas de setup inicial (Docker, CI/CD, backups, monitoreo) |
| **Mantenimiento** | Actualizaciones de seguridad, backups gestionados a mano |
| **Dominio + DNS** | Cloudflare Free ($0 + $10.44/año dominio) |
| **Email** | Resend Free (3000/mes) o Postmark |

> **Costo VPS mínimo:** **~€6-8/mes** ($7-10 USD) incluyendo todo.
> **Contras:** No hay managed DB (backups manuales), no hay auto-scaling, responsabilidad operativa, downtime en deploys si no se configura bien.
> **Pros:** Costo 3-4x menor que PaaS, control total, conocimiento de infraestructura.

### Alternativa Hetzner + Supabase

Combinación interesante:
- **VPS Hetzner CAX11** (~€5/mes) → FastAPI + Nginx
- **Supabase Pro** ($25/mes) → DB + Auth managed
- **Vercel Hobby** ($0) → Frontend
- **Cloudflare** ($0) → DNS

> **Total: ~$30/mes.** Lo mejor de ambos mundos: DB sin mantenimiento y compute barato.

---

## 5. Tabla Comparativa — Escenarios Completos

| Concepto | 🥇 **PaaS mínimo** | 🥈 **Híbrido** | 🥉 **VPS total** |
|---|---|---|---|
| **Frontend** | Vercel Hobby — $0 | Vercel Hobby — $0 | Hetzner CX — ~€6 |
| **Backend** | Railway Hobby — $5 | Hetzner CAX11 — ~€5 | (incluido en VPS) |
| **Base de datos** | Supabase Pro — $25 | Supabase Pro — $25 | Postgres auto-gestionado |
| **Auth** | Incluido en Supabase | Incluido en Supabase | Custom o Supabase Free |
| **DNS/CDN** | Cloudflare Free — $0 | Cloudflare Free — $0 | Cloudflare Free — $0 |
| **Dominio** | ~$0.87/mes ($10.44/año) | ~$0.87/mes | ~$0.87/mes |
| **Email** | $0 (Resend Free) | $0 (Resend Free) | $0 (Resend Free) |
| **Mantenimiento** | Mínimo (manejado) | Medio (solo VPS) | Alto (full ops) |
| **Escalabilidad** | Automática | Semi-automática | Manual (Docker) |

| **Total mensual** | **~$31/mes** | **~$30/mes** | **~$7-10/mes** |
|---|---|---|---|
| **Total anual** | ~$372 + dominio | ~$360 + dominio | ~$84-120 + dominio |

---

## 6. Proyección Escala Media (6-12 meses)

Cuando el sistema esté en producción real con usuarios activos (~15-20 usuarios concurrentes, reportes diarios, movimiento de inventario):

| Servicio | Upgrade | Costo/mes |
|---|---|---|
| **Supabase** | Se mantiene Pro ($25). 8 GB DB y 250 GB egress es mucho para datos transaccionales. Solo si crece mucho la DB, considerar Team ($75). | $25 |
| **Railway** | Upgrade a Pro ($20/mes) si se necesita más RAM o varias réplicas. Si el backend sigue liviano, el Hobby ($5) sigue alcanzando. | $5-20 |
| **Vercel** | Se mantiene Hobby ($0). Si se agregan preview deployments por equipo, Pro ($20). | $0-20 |
| **Resend** | Pro ($20/mes) si se envían >3.000 emails/mes (reportes diarios + notificaciones). | $0-20 |
| **Dominio** | Se mantiene. | $0.87 |
| **Total** | — | **~$31-86/mes** |

---

## 7. Recomendación Final

### Para empezar (meses 1-6):

```
🚀 Stack recomendado: PaaS mínimo

Supabase Pro       $25/mes  ← DB + Auth managed (no te preocupes por backups)
Railway Hobby       $5/mes  ← Backend FastAPI (los $5 de crédito cubren el mes)
Vercel Hobby        $0/mes  ← Frontend React (no hay razón para pagar)
Cloudflare Free     $0/mes  ← DNS + CDN + SSL
Resend Free         $0/mes  ← 3.000 emails/mes alcanza
Dominio .com     ~$0.87/mes  ← Cloudflare o Porkbun

                   $31/mes
```

**Por qué esta combinación:**
- **Supabase Pro** — DB managed con backups automáticos (7 días), auth incluido, 8 GB que sobran para datos transaccionales de una planta textil.
- **Railway Hobby** — El backend FastAPI liviano consume menos de $5/mes en recursos, el crédito cubre. No hay que configurar servidor.
- **Vercel Hobby —** Es gratis para proyectos públicos/equipos pequeños. Builds automáticos desde Git.
- **Cloudflare Free** — DNS rápido, DDoS protection de nivel enterprise, SSL gratis. Sin contras.
- **Resend Free** — 3.000 emails/mes para password resets y notificaciones iniciales.

### Para considerar VPS:

**Solo si:** Alguien del equipo tiene experiencia operativa con Linux, Docker, Postgres, y quiere ahorrar ~$20-25/mes a cambio de ~2-4 horas/mes de mantenimiento. Si no hay esa experiencia, los $31/mes del PaaS son un precio irrisorio comparado con el tiempo que te ahorra.

### Costos únicos / setup:

| Concepto | Costo estimado |
|---|---|
| Dominio (1er año) | $10-11 |
| Configuración inicial CI/CD | 2-4 horas dev |
| Setup Supabase (migraciones, auth) | Incluido en $25/mes |
| Setup Vercel + dominio custom | 30 min |
| **Total inicial** | **~$10 + tiempo dev** |

### Notas adicionales

- **Supabase Free** sirve para staging/desarrollo. En producción ir directo a Pro por los backups automáticos (7 días de PITR).
- **Railway** y **Render** son intercambiables. Render Starter ($7/mes) no duerme servicios. Probar cual funciona mejor con FastAPI.
- **Considerar región:** Supabase tiene región en **São Paulo (sudeste de Sudamérica)** y **Virginia (Norteamérica)**. Para una planta textil en Argentina, elegir São Paulo minimiza latencia. Railway también ofrece región en São Paulo. Vercel tiene edge global automático.
- **Los costos están en USD.** Dólar blue/CCL en Argentina puede encarecer la percepción local, pero los servicios se facturan en USD.
- **Facturación anual:** Donde esté disponible (dominio, Supabase, Railway), pagar anual puede ahorrar 15-20%.
- **No hay costos de licencias adicionales.** Todo el stack es open source (FastAPI, React, Postgres) y los servicios se cobran por infraestructura, no por licencias de software.

---

## 8. TCO Realista para el Comprador (CRÍTICO)

> Esta sección es la que **tenés que mostrarle al comprador**. No es el costo optimizado para un dev que administra su propio VPS. Es **el costo real** que un cliente promedio va a pagar mes a mes, incluyendo todo lo que un negocio necesita para operar sin sorpresas.

### 8.1 Costos que la mayoría de los presupuestos "baratos" omiten

| Concepto | Por qué se omite | Costo real/mes |
|---|---|---|
| **Entorno de staging/QA** | "Se puede usar el free tier" — hasta que hacés deploy de una migration que rompe prod porque no testeaste. | $15-25 |
| **Monitoreo + uptime** | "Cloudflare Free ya da" — pero no te avisa si el backend se cae a las 3 AM. Sentry + UptimeRobot. | $0-30 |
| **Email transaccional a escala** | "Resend Free 3.000/mes" — un reporte diario consolidado para 20 empleados + notificaciones puede ser 600-1.000 emails/mes. Sumale recovery de password, alertas. | $0-20 |
| **Dominio con renovación real** | "Pone Cloudflare a $10/año" — pero si el cliente quiere .com.ar, .com.uy, o TLDs especiales, el precio cambia. | $1-5 |
| **Certificado SSL dedicado** | Cloudflare lo da gratis — pero si el cliente no quiere depender de Cloudflare (o usa servicios que requieren SSL directo), hay que comprarlo. | $0-10 |
| **Soporte del proveedor** | Los planes Free no tienen SLA ni soporte. Si se cae Supabase/Railway/Vercel a las 2 AM, no hay a quién llamar. Los planes pagos con soporte cuestan más. | $20-50 extra |
| **Backups fuera del proveedor** | El backup de Supabase Pro cubre 7 días. Si querés backup diario a un bucket externo (S3, R2) para disaster recovery, es extra. | $0-5 |
| **Log retention** | Supabase Pro retiene 7 días. Para debugging de producción en una planta, 7 días puede ser poco. Team ($75/mes) da 28 días. | $0-50 extra |
| **Horas de mantenimiento** | Actualizaciones de seguridad, parches, migraciones de esquema. Si el cliente no tiene técnico interno, hay que cobrarlas. | 2-4 h/mes |

### 8.2 Escenario Realista — Cliente promedio sin técnico interno

El comprador NO sabe administrar servidores. No sabe qué es un VPS, no sabe Docker, no sabe hacer rollbacks. Todo tiene que funcionar automáticamente o con soporte.

| Concepto | Proveedor/Plan | Costo/mes |
|---|---|---|
| **Producción — DB + Auth** | Supabase Pro | **$25.00** |
| **Staging — DB + Auth** | Supabase Pro (2do proyecto, 8 GB) | **$25.00** |
| **Producción — Backend** | Railway Pro ($20 crédito, SIN sleep, 99.99%) | **$20.00** |
| **Staging — Backend** | Railway Hobby ($5 crédito, duerme tras inactividad) | **$5.00** |
| **Producción — Frontend** | Vercel Hobby | **$0.00** |
| **Staging — Frontend** | Vercel Hobby (proyecto separado o preview) | **$0.00** |
| **DNS + CDN** | Cloudflare Free | **$0.00** |
| **Dominio .com** | Cloudflare (~$10.44/año) | **$0.87** |
| **Email transaccional** | Resend Pro — 50.000 emails/mes | **$20.00** |
| **Error tracking** | Sentry — Team plan (10K eventos/mes, performance) | **$26.00** |
| **Monitoreo uptime** | UptimeRobot Free (5 monitores, 5 min) | **$0.00** |
| **Custom domain Supabase** | Add-on obligatorio si el cliente quiere su dominio | **$10.00** |
| **Backup externo (DR)** | Supabase PITR ($100/mes) o Cloudflare R2 (objeto) | **$0-100** |
| **Soporte Railway Pro** | Incluido en Pro (prioridad) | — |
| | | |
| **TOTAL PRODUCCIÓN + STAGING REALISTA** | — | **~$132/mes** |
| **Mantenimiento mensual estimado** | 2-4 h de un dev (actualizaciones, monitoreo, soporte) | Según tarifa |

### 8.3 Desglose por etapa de adopción

| Etapa | Situación | Costo/mes TCO real |
|---|---|---|
| **🧪 Piloto** | 1 planta, 5-8 usuarios, probando el sistema 3 meses. Sin staging todavía. | **~$56/mes** |
| **🚀 Producción básica** | 1 planta, 10-15 usuarios, staging + prod, email transaccional, monitoreo mínimo. | **~$132/mes** |
| **📈 Producción madura** | 1 planta grande, 20+ usuarios, PITR, retención de logs extendida, performance monitoring. | **~$200-280/mes** |
| **🏭 Multi-planta** | 2-3 plantas, cada una con su entorno, posible redundancia, compliance. | **$350+/mes** |

### 8.4 Costos que el comprador debe presupuestar aparte

| Concepto | Es una sola vez | Monto estimado |
|---|---|---|
| **Desarrollo e implementación** | Sí | A negociar |
| **Migración de datos históricos** | Sí, pero puede requerir soporte continuo | $500-3.000 según volumen |
| **Capacitación de usuarios** | Sí (primer lote) | $200-1.000 |
| **Configuración inicial de infraestructura** | Sí | $200-500 |
| **Soporte técnico mensual** (si no hay interno) | No — recurrente | $100-500/mes |
| **Ajustes y features post-entrega** | No — según demanda | A negociar |

### 8.5 Lo que NO está incluido (y podría aparecer)

| Concepto | Cuándo aparece | Costo potencial |
|---|---|---|
| **Redis / caché** | Si los reportes diarios se vuelven lentos con muchos datos históricos | $5-15/mes (Upstash / Railway Redis) |
| **Generación de PDFs** | Si el cliente quiere reportes descargables en PDF (certificados de calidad, órdenes) | $0-20/mes (depende de librería y compute) |
| **File storage para imágenes** | Fotos de productos, escaneos de documentos, firmas digitales | $0-10/mes (Supabase Storage 100 GB incluidos en Pro) |
| **Roles y permisos UI** | Si el cliente quiere gestionar usuarios desde el frontend (hoy es solo backend) | Tiempo dev, no infraestructura |
| **SSO / SAML** | Si el cliente es corporativo y requiere inicio de sesión con Azure AD / Google Workspace | $75/mes (Supabase Advanced MFA) o Enterprise |
| **Cumplimiento legal** | Protección de datos personales (LATAM: Ley de Protección de Datos), RGPD si aplica | Tiempo legal + dev, no infraestructura |
| **VPN / conexión segura** | Si el cliente quiere que SOLO accedan desde la red de la planta | $5-30/mes (Tailscale, Wireguard en VPS, o Cloudflare Zero Trust Free) |

### 8.6 Costo de oportunidad — el stack del comprador dueño de PyME

Pensalo así: el comprador promedio de este sistema es un dueño o gerente de una textil. No tiene equipo de IT. Cuando le decís "cuesta $31/mes", escucha "me sale dos sanguchitos de milanesa". Pero cuando llega la tarjeta con $132 + dominios + Sentry + el soporte que le tuviste que dar porque se le borró un lote... ahí empiezan los problemas.

**El número honesto para vender es:**

> "El sistema cuesta **~$130-150/mes** de infraestructura. El primer año, sumando setup y capacitación, estimá **$2.500-4.000** total entre desarrollo e implementación. Después, **$130-150/mes** más **2-4 horas de soporte** si no tenés quien lo mantenga."

Eso no es una estafa. Eso es transparencia. Y un comprador que sabe eso de antemano **no te va a reclamar después**.
