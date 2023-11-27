package org.example;

import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class ExpendedorSimpleTest {
    private ExpendedorSimple expendedorSimple;
    @BeforeEach
    void setUp() {
        expendedorSimple = new ExpendedorSimple(3);
    }

    @AfterEach
    void tearDown() {
    }

    @Test
    @DisplayName("Test Una Bebida")
    public void testComprarUnaBebida() throws Exception {
        System.out.println("comprarUnaBebida");
        int pago = 1000;
        assertNotNull(expendedorSimple.comprarBebida(pago));

    }

    @Test
    @DisplayName("Test Tres Bebida")
    public void testComprarTresBebida() throws Exception {
        int pago = 1000;
        assertNotNull(expendedorSimple.comprarBebida(pago));
        assertNotNull(expendedorSimple.comprarBebida(pago));
        assertNotNull(expendedorSimple.comprarBebida(pago));
    }

    @Test
    @DisplayName("Test NoHayBebidaException")
    public void testComprarCuatroBebida(){
        int pago = 1000;
        Exception exception = assertThrows(NoHayBebidaException.class,()->{
            expendedorSimple.comprarBebida(pago);
            expendedorSimple.comprarBebida(pago);
            expendedorSimple.comprarBebida(pago);
            expendedorSimple.comprarBebida(pago);
        });
    }

    @Test
    @DisplayName("Test PagoInsuficienteException")
    public void testComprarBebidaSinSuficienteMoneda(){
        int pago = 100;
        Exception exception = assertThrows(PagoInsuficienteException.class,
                ()->{
                    expendedorSimple.comprarBebida(pago);
                });
    }
}