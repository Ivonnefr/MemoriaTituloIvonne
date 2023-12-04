package org.example;

public class ArticuloConjurado extends Articulo{
    public ArticuloConjurado(String nombre, double diaRestante, double calidad) {
        super(nombre,diaRestante,calidad);
    }

    public void diaSiguiente(){
        if(this.diaRestante==0){
            this.setCalidad(this.calidad-4);
        }
        else{
            this.setDiaRestante(this.diaRestante-1);
        }

    }

}
