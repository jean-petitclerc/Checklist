# {{ cl.prep_cl_name }}
## Variables utilisées dans cette checklist
{% if cl_vars %}
| Nom de Variable | Valeur |
| :-------------- | :----- |
{% for cl_v in  cl_vars %}
| name | {{ cl_v['value'] }} |
{% endfor %}
{% else %}
Aucune variable utilisée dans cette checklist.
{% endif %}

## Sections
{% if sections %}
    {% for section in  sections %}

### {{ section['name'] }}
{{ section['detail'] }}
{% for step in section['steps'] %}

#### {{ step['short'] }}
{{ step['detail'] }}
Status: {{ step['status'] }}
Usager: {{ step['user'] }}
```
{{ step['code'] }}
```
{% if step['rslt'] %}
Résultat:
```
{{ step['rslt'] }}
```
{% endif %}
{% else %}
Pas d'étape dans cette section.
{% endfor %}
{% endfor %}
{% else %}
Aucune section dans cette checklist.
{% endif %}
