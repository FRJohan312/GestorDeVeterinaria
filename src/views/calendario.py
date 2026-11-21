"""DateEntry con limpieza del cambio de tema diferido al destruir el formulario."""

from tkcalendar import DateEntry
from babel import localedata


class CalendarioFecha(DateEntry):
    def __init__(self, master=None, *, permitir_vacio=False, **opciones):
        self._permitir_vacio = permitir_vacio
        self._cambio_tema_pendiente = None
        opciones.setdefault("date_pattern", "yyyy-mm-dd")
        opciones.setdefault("locale", next((idioma for idioma in ("es_ES", "es") if localedata.exists(idioma)), "en_US"))
        opciones.setdefault("state", "readonly")
        opciones.setdefault("firstweekday", "monday")
        super().__init__(master, **opciones)
        # tkcalendar 1.6.1 no cancela este temporizador en DateEntry.destroy().
        self.bind("<<ThemeChanged>>", self._programar_cambio_tema)

    def _validate_date(self):
        if self._permitir_vacio and not self.get().strip():
            return True
        return super()._validate_date()

    def drop_down(self):
        if not self._permitir_vacio or self.get().strip():
            return super().drop_down()
        # DateEntry vuelve a interpretar el texto después de validarlo. Le damos
        # una fecha de referencia solo para abrir/cerrar, sin activar el filtro.
        self._set_text(self.format_date(self._date))
        try:
            return super().drop_down()
        finally:
            self._set_text("")

    def _programar_cambio_tema(self, event=None):
        if self._cambio_tema_pendiente is not None:
            self.after_cancel(self._cambio_tema_pendiente)
        self._cambio_tema_pendiente = self.after(10, self._actualizar_tema)

    def _actualizar_tema(self):
        self._cambio_tema_pendiente = None
        self._on_theme_change()

    def destroy(self):
        if self._cambio_tema_pendiente is not None:
            self.after_cancel(self._cambio_tema_pendiente)
            self._cambio_tema_pendiente = None
        super().destroy()
