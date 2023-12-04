package org.example;
import java.util.ArrayList;
import java.util.List;

public class TiendaMagica {
    private double fondo;
    private List<Articulo> articulos;
    private final static double VALOR_COMPRA = 0.4;

    public TiendaMagica(double fondoInicial) {
        this.fondo = fondoInicial;
        this.articulos = new ArrayList<>();
    }

    public List<Articulo> getArticulos() {
        return articulos;
    }

    public void comprarArticulo(Articulo articulo) throws FondoInsuficienteException {
        double costo = articulo.getValor()*VALOR_COMPRA;
        if (fondo >= costo) {
            articulos.add(articulo);
            fondo -= costo;
        } else {
            throw new FondoInsuficienteException("Fondos insuficientes para comprar el artículo: " + articulo.getNombre());
        }
    }

    public void venderArticulo(Articulo articulo) {
        articulos.remove(articulo);
        fondo += articulo.getValor();
    }

    public double getFondo() {
        return fondo;
    }

    public void diaSiguiente() {
        ArrayList<Articulo> toRemove = new ArrayList<>();
        for (Articulo articulo : articulos) {
          articulo.diaSiguiente();
          if(articulo.getCalidad()==0){
            toRemove.add(articulo);
          }
        }
        articulos.removeAll(toRemove);
    }
}
