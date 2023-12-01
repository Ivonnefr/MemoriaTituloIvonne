package org.example;

public class Articulo {
    protected String nombre;
    protected int diaRestante;
    protected double calidad;
    private final static int CALIDAD_MAX = 100;
    
    public Articulo(String nombre, int diaRestante, double calidad) {
        this.nombre = nombre;
        this.setDiaRestante(diaRestante);
        this.setCalidad(calidad);
    }

    public String getNombre() {
        return nombre;
    }

    public int getDiaRestante() {
        return diaRestante;
    }

    public void setDiaRestante(int diaRestante) {
        this.diaRestante = Math.max(0, diaRestante);
    }

    public double getCalidad() {
        return calidad;
    }

    public void setCalidad(double calidad) {
        this.calidad = Math.max(0, Math.min(CALIDAD_MAX, calidad));
    }

    public double getValor() {
        // Valor es 2 veces la calidad
        return calidad * 2;
    }

    public void diaSiguiente(){
        if(this.diaRestante==0){
            this.setCalidad(this.calidad-2);
        }
        else{
            this.setCalidad(this.calidad-1);
            this.setDiaRestante(this.diaRestante-1);
        }

    }
}
