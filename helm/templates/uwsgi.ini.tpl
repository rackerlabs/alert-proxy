apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ include "alert-proxy.fullname" . }}-uwsgi-config
  namespace: {{ .Values.namespace }}
  labels:
    {{- include "alert-proxy.labels" . | nindent 4 }}
data:
  uwsgi.ini: |
    [uwsgi]
    module = {{ .Values.uwsgi.module | default "wsgi:app" }}
    uid = {{ .Values.uwsgi.uid | default "alert-proxy" }}
    gid = {{ .Values.uwsgi.gid | default "alert-proxy" }}
    http = 0.0.0.0:{{ .Values.uwsgi.httpPort | default 8000 }}
    master = {{ .Values.uwsgi.master | default true }}
    processes = {{ .Values.uwsgi.processes | default 4 }}
    threads = {{ .Values.uwsgi.threads | default 1 }}
    vacuum = {{ .Values.uwsgi.vacuum | default true }}
    die-on-term = {{ .Values.uwsgi.dieOnTerm | default true }}
    disable-logging = {{ .Values.uwsgi.disableLogging | default true }}
