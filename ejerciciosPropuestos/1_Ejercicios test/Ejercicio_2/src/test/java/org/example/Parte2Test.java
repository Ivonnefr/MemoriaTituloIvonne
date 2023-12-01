import org.example.Articulo;
import org.example.ArticuloComun;
import org.example.FondoInsuficienteException;
import org.example.TiendaMagica;
import org.junit.jupiter.api.Test;
import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

public class Parte2Test {


    @Test
    public void testCalidadComun() throws FondoInsuficienteException {
        TiendaMagica tienda = new TiendaMagica(100);
        Articulo articulo = new ArticuloComun("Poción", 2, 2);
        Articulo articulo2 = new ArticuloComun("Poción2", 15, 15.0);
        tienda.comprarArticulo(articulo);
        tienda.comprarArticulo(articulo2);
        tienda.diaSiguiente();
        assertEquals(1, articulo.getCalidad(), "La calidad no ha bajado correctamente");
        tienda.diaSiguiente();
        assertEquals(0, articulo.getCalidad(), "La calidad no ha bajado correctamente");
        tienda.diaSiguiente();
        assertEquals(0, articulo.getCalidad(), "La calidad no puede ser inferior a 0");
        assertEquals(12, articulo2.getCalidad(), "La calidad no ha bajado correctamente");
        Articulo articulo3 = new ArticuloComun("Poción", 2, 200);
        assertEquals(50, articulo3.getCalidad(), "La calidad de un artículo común no puede ser superior a 50");
    }

    @Test
    public void testFondo() throws FondoInsuficienteException {
        TiendaMagica tienda = new TiendaMagica(100);
        assertEquals(100, tienda.getFondo(), "Los fondos no se gestionan adecuadamente");
        Articulo articulo = new Articulo("Poción", 2, 2);
        tienda.comprarArticulo(articulo);
        assertEquals((100-(4*0.4)), tienda.getFondo(), "Los fondos no se gestionan adecuadamente");
        Articulo articulo2 = new Articulo("Poción2", 15, 15.0);
        tienda.comprarArticulo(articulo2);
        assertEquals((100-4*0.4-30*0.4), tienda.getFondo(), "Los fondos no se gestionan adecuadamente");
    }

    @Test
    public void testFondoException(){
        TiendaMagica tienda = new TiendaMagica(20);
        Articulo articulo = new Articulo("Poción", 15, 100.0);

        assertThrows(FondoInsuficienteException.class, () -> {
            tienda.comprarArticulo(articulo);
        },"No se lanza la excepción para la compra de un artículo sin los fondos necesarios");
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
    public void testDobleCalidad() throws FondoInsuficienteException {
        TiendaMagica tienda = new TiendaMagica(100);
        Articulo articulo = new Articulo("Poción", 2, 30);
        tienda.comprarArticulo(articulo);
        tienda.diaSiguiente();
        assertEquals(29, articulo.getCalidad(), "La calidad no ha bajado correctamente");
        tienda.diaSiguiente();
        assertEquals(28, articulo.getCalidad(), "La calidad no ha bajado correctamente");
        tienda.diaSiguiente();
        assertEquals(26, articulo.getCalidad(), "La calidad no ha bajado correctamente con diaRestante == 0.");
        tienda.diaSiguiente();
        assertEquals(24, articulo.getCalidad(), "La calidad no ha bajado correctamente con diaRestante == 0.");
    }

    @Test
    public void testValorACero() throws FondoInsuficienteException {
        TiendaMagica tienda = new TiendaMagica(100);
        Articulo articulo = new Articulo("Poción", 10, 1);
        tienda.comprarArticulo(articulo);
        Articulo articulo2 = new Articulo("Poción", 1, 6);
        tienda.comprarArticulo(articulo2);
        List<Articulo> articulos = tienda.getArticulos();
        assertEquals(2,articulos.size(),"Los artículos no se añaden correctamente a la lista recuperada en getArticulos.");
        tienda.diaSiguiente();
        assertEquals(1,articulos.size(),"Quedan artículos con una calidad de 0 en la lista.");
        tienda.diaSiguiente();
        tienda.diaSiguiente();
        tienda.diaSiguiente();
        assertEquals(0,articulos.size(),"Quedan artículos con una calidad de 0 en la lista.");
    }

    @Test
    public void testDobleCalidadComun() throws FondoInsuficienteException {
        TiendaMagica tienda = new TiendaMagica(100);
        Articulo articulo = new ArticuloComun("Poción", 2, 30);
        tienda.comprarArticulo(articulo);
        tienda.diaSiguiente();
        assertEquals(29, articulo.getCalidad(), "La calidad de ArticuloComun no ha bajado correctamente");
        tienda.diaSiguiente();
        assertEquals(28, articulo.getCalidad(), "La calidad de ArticuloComun no ha bajado correctamente");
        tienda.diaSiguiente();
        assertEquals(26, articulo.getCalidad(), "La calidad de ArticuloComun no ha bajado correctamente con diaRestante == 0.");
        tienda.diaSiguiente();
        assertEquals(24, articulo.getCalidad(), "La calidad de ArticuloComun no ha bajado correctamente con diaRestante == 0.");
    }
}