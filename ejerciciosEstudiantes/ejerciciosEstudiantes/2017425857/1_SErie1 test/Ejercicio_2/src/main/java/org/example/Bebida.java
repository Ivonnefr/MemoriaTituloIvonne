package org.example;

abstract class Bebida{

    private int serie;

    public Bebida(int serie) {
        this.serie = serie;
    }

    public abstract String beber();

    public int getSerie() {
        return serie;
    }



} 
