package org.example;

public class ArticuloComun extends Articulo{
    private final static int CALIDAD_MAX = 50;
    public ArticuloComun(String nombre, double diaRestante, double calidad) {
        super(nombre,diaRestante,calidad);
    }

    public void setCalidad(double calidad) {
        this.calidad = Math.max(0, Math.min(CALIDAD_MAX, calidad));
    }

}
