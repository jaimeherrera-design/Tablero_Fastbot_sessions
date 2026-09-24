# Fastbot Sessions

Dashboard para consolidar y monitorear automáticamente los archivos CSV de sesiones ubicados en la raíz del proyecto.

## Ejecución

```powershell
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

La aplicación descubre todos los archivos `*.csv` al iniciar. Para incorporar un nuevo corte, déjalo en esta misma carpeta y recarga el navegador. Las filas completamente idénticas entre archivos se contabilizan una sola vez; las filas con igual fecha, hora y dimensiones, pero métricas diferentes, se conservan como agregados distintos del origen.

## Estructura de los CSV

Cada archivo debe incluir estas columnas:

```text
session_start_fecha,session_start_hora,duracion_total,user_started_session,not_available_agent_session,category,agent_id,bsuid,botname,operator_id,cuenta
```

Las fechas deben ser interpretables por pandas y las horas deben estar entre 0 y 23. Los conteos vacíos se consideran cero, las métricas negativas se ajustan a cero y los registros sin fecha u hora válida se descartan.

## Métricas

- Total de sesiones mediante la suma de `cuenta`.
- Total y tasa de sesiones iniciadas por usuario mediante `user_started_session`.
- Total y tasa de sesiones sin agente disponible mediante `not_available_agent_session`.
- Duración promedio por sesión presentada en formato `HH:MM:SS` (el campo de origen está en minutos).
- Comparación MTD contra el mismo día de corte del mes anterior.
- Variaciones por mes, día y hora para cada métrica.
- Participación y filtros por bot, categoría, operador y agente.
- Mapas de calor por día de la semana y hora para volumen y tasas.
- Matriz temporal e insights operativos dinámicos.