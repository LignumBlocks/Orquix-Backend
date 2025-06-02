# Estrategia de Backup de Base de Datos - Orquix Backend MVP

## Resumen Ejecutivo

Este documento define la estrategia básica de backup para la base de datos PostgreSQL con pgvector de Orquix Backend en su fase MVP. La estrategia está diseñada para ser simple, confiable y escalable.

## Arquitectura de Datos

### Base de Datos Principal
- **Motor**: PostgreSQL 15+ con extensión pgvector
- **Esquema MVP**: 6 tablas principales
- **Datos Críticos**: 
  - Usuarios y proyectos
  - Interacciones y respuestas IA
  - Embeddings vectoriales (context_chunks)
  - Síntesis moderadas

### Criticidad de Datos

| Tabla | Criticidad | Justificación |
|-------|------------|---------------|
| `users` | **CRÍTICA** | Datos de autenticación y perfil |
| `projects` | **CRÍTICA** | Configuración y metadatos de proyectos |
| `interaction_events` | **ALTA** | Historial de interacciones del usuario |
| `moderated_syntheses` | **ALTA** | Resultados procesados de IA |
| `context_chunks` | **MEDIA** | Regenerable pero costoso |
| `ia_responses` | **BAJA** | Datos de debugging y métricas |

## Estrategia de Backup MVP

### 1. Backup Completo Diario

**Frecuencia**: Cada día a las 02:00 UTC
**Retención**: 30 días
**Método**: `pg_dump` con compresión

```bash
#!/bin/bash
# Script: daily_backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/orquix"
DB_NAME="orquix_db"
DB_USER="orquix_user"

# Crear directorio si no existe
mkdir -p $BACKUP_DIR

# Backup completo con compresión
pg_dump -h localhost -U $DB_USER -d $DB_NAME \
  --format=custom \
  --compress=9 \
  --verbose \
  --file="$BACKUP_DIR/orquix_full_$DATE.dump"

# Verificar integridad del backup
pg_restore --list "$BACKUP_DIR/orquix_full_$DATE.dump" > /dev/null

if [ $? -eq 0 ]; then
    echo "✅ Backup exitoso: orquix_full_$DATE.dump"
else
    echo "❌ Error en backup: orquix_full_$DATE.dump"
    exit 1
fi

# Limpiar backups antiguos (>30 días)
find $BACKUP_DIR -name "orquix_full_*.dump" -mtime +30 -delete
```

### 2. Backup Incremental de Datos Críticos

**Frecuencia**: Cada 6 horas
**Retención**: 7 días
**Método**: Backup selectivo de tablas críticas

```bash
#!/bin/bash
# Script: incremental_backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/orquix/incremental"
DB_NAME="orquix_db"
DB_USER="orquix_user"

mkdir -p $BACKUP_DIR

# Backup solo de tablas críticas
pg_dump -h localhost -U $DB_USER -d $DB_NAME \
  --format=custom \
  --compress=9 \
  --table=users \
  --table=projects \
  --table=interaction_events \
  --table=moderated_syntheses \
  --file="$BACKUP_DIR/orquix_critical_$DATE.dump"

# Limpiar backups incrementales antiguos (>7 días)
find $BACKUP_DIR -name "orquix_critical_*.dump" -mtime +7 -delete
```

### 3. Backup de Embeddings (Semanal)

**Frecuencia**: Domingos a las 01:00 UTC
**Retención**: 4 semanas
**Método**: Backup específico de context_chunks

```bash
#!/bin/bash
# Script: embeddings_backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/orquix/embeddings"
DB_NAME="orquix_db"
DB_USER="orquix_user"

mkdir -p $BACKUP_DIR

# Backup de embeddings con compresión máxima
pg_dump -h localhost -U $DB_USER -d $DB_NAME \
  --format=custom \
  --compress=9 \
  --table=context_chunks \
  --file="$BACKUP_DIR/orquix_embeddings_$DATE.dump"

# Limpiar backups de embeddings antiguos (>4 semanas)
find $BACKUP_DIR -name "orquix_embeddings_*.dump" -mtime +28 -delete
```

## Procedimientos de Restauración

### Restauración Completa

```bash
# 1. Detener la aplicación
sudo systemctl stop orquix-backend

# 2. Crear base de datos limpia
dropdb orquix_db
createdb orquix_db

# 3. Restaurar desde backup
pg_restore -h localhost -U orquix_user -d orquix_db \
  --verbose \
  --clean \
  --if-exists \
  /backups/orquix/orquix_full_YYYYMMDD_HHMMSS.dump

# 4. Verificar extensiones
psql -h localhost -U orquix_user -d orquix_db -c "CREATE EXTENSION IF NOT EXISTS vector;"

# 5. Ejecutar migraciones si es necesario
cd /app && poetry run alembic upgrade head

# 6. Reiniciar aplicación
sudo systemctl start orquix-backend
```

### Restauración Selectiva (Solo Datos Críticos)

```bash
# Restaurar solo tablas específicas
pg_restore -h localhost -U orquix_user -d orquix_db \
  --verbose \
  --table=users \
  --table=projects \
  /backups/orquix/incremental/orquix_critical_YYYYMMDD_HHMMSS.dump
```

## Monitoreo y Alertas

### Verificación de Integridad

```bash
#!/bin/bash
# Script: verify_backup.sh

LATEST_BACKUP=$(ls -t /backups/orquix/orquix_full_*.dump | head -1)

# Verificar que el backup se puede listar
pg_restore --list "$LATEST_BACKUP" > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo "✅ Backup íntegro: $LATEST_BACKUP"
else
    echo "❌ Backup corrupto: $LATEST_BACKUP"
    # Enviar alerta (email, Slack, etc.)
fi
```

### Métricas de Backup

- **Tamaño del backup**: Monitorear crecimiento
- **Tiempo de ejecución**: Detectar degradación
- **Tasa de éxito**: Alertar en fallos
- **Espacio disponible**: Prevenir fallos por espacio

## Configuración de Cron

```bash
# Editar crontab: crontab -e

# Backup completo diario a las 02:00 UTC
0 2 * * * /scripts/daily_backup.sh >> /var/log/orquix_backup.log 2>&1

# Backup incremental cada 6 horas
0 */6 * * * /scripts/incremental_backup.sh >> /var/log/orquix_backup.log 2>&1

# Backup de embeddings semanal (domingos 01:00 UTC)
0 1 * * 0 /scripts/embeddings_backup.sh >> /var/log/orquix_backup.log 2>&1

# Verificación de integridad diaria a las 03:00 UTC
0 3 * * * /scripts/verify_backup.sh >> /var/log/orquix_backup.log 2>&1
```

## Consideraciones de Seguridad

### Encriptación
- **En tránsito**: Usar SSL para conexiones de backup
- **En reposo**: Encriptar backups con GPG

```bash
# Ejemplo de backup encriptado
pg_dump ... | gzip | gpg --cipher-algo AES256 --compress-algo 1 \
  --symmetric --output "backup_encrypted_$DATE.dump.gz.gpg"
```

### Acceso
- **Credenciales**: Usar variables de entorno o archivos .pgpass
- **Permisos**: Restringir acceso a archivos de backup (600)
- **Ubicación**: Almacenar backups en ubicación separada del servidor principal

## Escalabilidad Futura

### Para Producción
1. **Backup continuo**: Implementar WAL-E o pgBackRest
2. **Réplicas**: Configurar streaming replication
3. **Almacenamiento en la nube**: AWS S3, Google Cloud Storage
4. **Automatización**: Terraform/Ansible para infraestructura
5. **Monitoreo avanzado**: Prometheus + Grafana

### Estimaciones de Crecimiento

| Métrica | MVP | 6 meses | 1 año |
|---------|-----|---------|-------|
| Usuarios | 100 | 1,000 | 5,000 |
| Proyectos | 500 | 5,000 | 25,000 |
| Interacciones/día | 1,000 | 10,000 | 50,000 |
| Tamaño DB | 1 GB | 10 GB | 50 GB |
| Tiempo backup | 5 min | 30 min | 2 horas |

## Procedimientos de Emergencia

### Corrupción de Datos
1. Detener aplicación inmediatamente
2. Evaluar alcance de la corrupción
3. Restaurar desde último backup íntegro
4. Aplicar logs de transacciones si están disponibles
5. Validar integridad post-restauración

### Pérdida de Servidor
1. Provisionar nuevo servidor
2. Instalar PostgreSQL + pgvector
3. Restaurar desde backup más reciente
4. Reconfigurar aplicación
5. Validar funcionalidad completa

## Contactos de Emergencia

- **DBA Principal**: [email]
- **DevOps**: [email]
- **Escalación**: [email]

---

**Última actualización**: Junio 2025
**Próxima revisión**: Septiembre 2025 