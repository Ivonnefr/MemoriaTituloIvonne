package org.example;

public class ArticuloLegendario extends Articulo{
    private final static int CALIDAD_MAX = 300;
    public ArticuloLegendario(String nombre) {
        super(nombre,Double.POSITIVE_INFINITY,CALIDAD_MAX);
    }

    public void setCalidad(double calidad) {
        this.calidad = CALIDAD_MAX;
    }

}
