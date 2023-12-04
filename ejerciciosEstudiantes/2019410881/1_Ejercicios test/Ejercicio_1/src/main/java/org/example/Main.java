package org.example;

public class Main {
    public static void main(String[] args) {
        // Ejemplo de uso:
        TiendaMagica tienda = new TiendaMagica(300); // Comenzando con 1000 fondos
        Articulo item1 = new Articulo("Poción", 5, 20);
        Articulo item2 = new Articulo("Varita", 10, 40);

        System.out.println("Fondos actuales: " + tienda.getFondo());
        System.out.println("Artículos actuales: " + tienda.getArticulos());

        try {
            tienda.comprarArticulo(item1);
            tienda.comprarArticulo(item2);
            tienda.comprarArticulo(new Articulo("ObjetoCaro", 3, 100)); // Esto lanzará FondoInsuficienteException
        } catch (FondoInsuficienteException e) {
            System.out.println("Error: " + e.getMessage());
        }



        // Avanzar un día
        tienda.diaSiguiente();

        // Mostrar el estado después de un día
        System.out.println("Después de un día:");
        System.out.println("Fondos actuales: " + tienda.getFondo());
        System.out.println("Artículos actuales: " + tienda.getArticulos());
    }
}