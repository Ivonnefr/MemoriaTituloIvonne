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
//asasdasd
    public Sprite comprarBebida(int pago) throws NoHayBebidaException, PagoInsuficienteException{
        if (sprites.isEmpty()) throw new NoHayBebidaException();
        if (pago > precio) throw new PagoInsuficienteException();
            return sprites.remove(sprites.size()-1);
    }
}
