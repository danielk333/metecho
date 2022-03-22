{{ fullname | escape }}
{{ (fullname | escape | length)*"=" }}

.. currentmodule:: {{ module }}

.. autoclass:: {{ objname }}


{% block attributes %}
{% if attributes %}
Attributes
----------

{% for item in attributes %}
.. autoattribute:: {{ name }}.{{ item }}
    :noindex:
{%- endfor %}
{% endif %}
{% endblock %}


{% block methods %}
{% if methods %}
Methods
-------

{% for item in methods %}
.. automethod:: {{ name }}.{{ item }}
    :noindex:
{%- endfor %}
{% endif %}
{% endblock %}