

import org.example.Articulo;
import org.example.FondoInsuficienteException;
import org.example.TiendaMagica;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

public class Parte1Test {

    @Test
    public void testGetValorDeUnArticulo() {
        Articulo articulo = new Articulo("Poción", 5, 20.0);
        assertEquals(40.0, articulo.getValor(), "El valor de un artículo debe ser el doble de su calidad");
    }

    @Test
    public void testDiaRestante() throws FondoInsuficienteException {
        TiendaMagica tienda = new TiendaMagica(100);
        Articulo articulo = new Articulo("Poción", 2, 20.0);
        Articulo articulo2 = new Articulo("Poción2", 15, 20.0);
        tienda.comprarArticulo(articulo);
        tienda.comprarArticulo(articulo2);
        tienda.diaSiguiente();
        assertEquals(1, articulo.getDiaRestante(), "El número de días restantes no ha bajado correctamente");
        tienda.diaSiguiente();
        assertEquals(0, articulo.getDiaRestante(), "El número de días restantes no ha bajado correctamente");
        tienda.diaSiguiente();
        assertEquals(0, articulo.getDiaRestante(), "El número de días restantes no puede ser inferior a 0");
        assertEquals(12, articulo2.getDiaRestante(), "El número de días restantes no ha bajado correctamente");
    }

    @Test
    public void testCalidad() throws FondoInsuficienteException {
        TiendaMagica tienda = new TiendaMagica(100);
        Articulo articulo = new Articulo("Poción", 2, 2);
        Articulo articulo2 = new Articulo("Poción2", 15, 15.0);
        tienda.comprarArticulo(articulo);
        tienda.comprarArticulo(articulo2);
        tienda.diaSiguiente();
        assertEquals(1, articulo.getCalidad(), "La calidad no ha bajado correctamente");
        tienda.diaSiguiente();
        assertEquals(0, articulo.getCalidad(), "La calidad no ha bajado correctamente");
        tienda.diaSiguiente();
        assertEquals(0, articulo.getCalidad(), "La calidad no puede ser inferior a 0");
        assertEquals(12, articulo2.getCalidad(), "La calidad no ha bajado correctamente");
        Articulo articulo3 = new Articulo("Poción", 2, 200);
        assertEquals(100, articulo3.getCalidad(), "La calidad no puede ser superior a 100");
    }



    @Test
    public void testFondo() throws FondoInsuficienteException {
        TiendaMagica tienda = new TiendaMagica(100);
        assertEquals(100, tienda.getFondo(), "Los fondos no se gestionan adecuadamente");
        Articulo articulo = new Articulo("Poción", 2, 2);
        tienda.comprarArticulo(articulo);
        assertEquals(96, tienda.getFondo(), "Los fondos no se gestionan adecuadamente");
        Articulo articulo2 = new Articulo("Poción2", 15, 15.0);
        tienda.comprarArticulo(articulo2);
        assertEquals(66, tienda.getFondo(), "Los fondos no se gestionan adecuadamente");
        Articulo articulo3 = new Articulo("Poción3", 15, 33.0);
        tienda.comprarArticulo(articulo3);
        assertEquals(0, tienda.getFondo(), "Los fondos no se gestionan adecuadamente");
    }

    @Test
    public void testFondoException(){
        TiendaMagica tienda = new TiendaMagica(100);
        Articulo articulo = new Articulo("Poción", 15, 100.0);

        assertThrows(FondoInsuficienteException.class, () -> {
            tienda.comprarArticulo(articulo);
        },"No se lanza la excepción para la compra de un artículo sin los fondos necesarios");
    }
}