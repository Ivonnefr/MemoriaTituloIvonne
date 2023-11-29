package org.example;

import java.util.ArrayList;

public class ExpendedorSimple {
    ArrayList<Sprite> sprites;
    private static int precio = 1000;

    public ExpendedorSimple(int size) {
        sprites = new ArrayList<Sprite>();
        for (int i = 0; i < size; i++) {
            sprites.add(new Sprite(i));
        }
    }

    public Bebida comprarBebida(int pago) throws NoHayBebidaException, PagoInsuficienteException{
        if (sprites.isEmpty()) throw new NoHayBebidaException("No hay bebida");
        if (pago > precio) throw new PagoInsuficienteException("pago insuficiente");
        return sprites.remove(sprites.size()-1);
    }

}
