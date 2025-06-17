{{- /* Example displaying a custom JSON payload for a webhook contact point.*/ -}}
{{- /* Edit the template name and template content as needed. */ -}}
{{- /* Variables defined in the webhook contact point can be accessed in .Vars but will not be previewable. */ -}}
{{ define "webhook.simon.payload" -}}
  {{ coll.Dict
  "status" .Status
  "alerts" (tmpl.Exec "webhook.simon.simple_alerts" .Alerts | data.JSON)
  | data.ToJSONPretty " "}}
{{- end }}

{{- /* Example showcasing embedding json templates in other json templates. */ -}}
{{ define "webhook.simon.simple_alerts" -}}
  {{- $alerts := coll.Slice -}}
  {{- range . -}}
    {{ $alerts = coll.Append (coll.Dict
    "status" .Status
    "labels" .Labels
    "startsAt" .StartsAt.Unix
    ) $alerts}}
  {{- end -}}
  {{- $alerts | data.ToJSON -}}
{{- end }}