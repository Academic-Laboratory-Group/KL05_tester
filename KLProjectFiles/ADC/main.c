#include "MKL05Z4.h"
#include "uart.h"
#include "ADC.h"

char rx_buf[]={0x20,0x20,0x20,0x20,0x20,0x20,0x20,0x20,0x20,0x20,0x20,0x20,0x20,0x20,0x20,0x20,0x20};

char tmp;

volatile int ADC_Channel;

uint8_t receive=1;

// UART interupt
void UART0_IRQHandler()
{
	if(UART0->S1 & UART0_S1_RDRF_MASK)
	{
		tmp=UART0->D;
		if(!receive)
		{
			rx_buf[0] = tmp;
			receive=1;
		}
	}
	NVIC_EnableIRQ(UART0_IRQn);
}

uint8_t wynik_ok=1;
uint16_t temp;

int wynik = 2137;

// ADC interupt
void ADC0_IRQHandler()
{	
	temp = ADC0->R[0];
	if(!wynik_ok)
	{
		wynik = temp;
		wynik_ok=1;
	}
	
	NVIC_EnableIRQ(ADC0_IRQn);
}

int main (void)
{	
	UART0_Init();
	
	uint8_t	kal_error;
	kal_error=ADC_Init();
	if(kal_error)
	{
		while(!(UART0->S1 & UART0_S1_TDRE_MASK));
		UART0->D = '9';
		while(1);
	}
	
	
	ADC_Channel = 11;
	ADC0->SC1[0] = ADC_SC1_AIEN_MASK;
	
	while(1)
	{
		if(receive)
		{
			if (rx_buf[0] == '0'){
				// read value from ADC_Channel
				wynik_ok = 0;
				
				ADC0->SC1[0] = ADC_SC1_AIEN_MASK | ADC_SC1_ADCH(ADC_Channel);
				while(!wynik_ok);
				
				int num = 1000;
				for (int i = 3; i>=0 ; i--)
				{
					while(!(UART0->S1 & UART0_S1_TDRE_MASK));
					UART0->D = (char)((wynik / num ) % 10 + 48);
					num /= 10;
				}
					
				while(!(UART0->S1 & UART0_S1_TDRE_MASK));
				UART0->D = '\r';
				while(!(UART0->S1 & UART0_S1_TDRE_MASK));
				UART0->D = '\n';
			}
			// change to coresponding ADC_Channel
			if (rx_buf[0] == '1'){
				while(!(UART0->S1 & UART0_S1_TDRE_MASK));
				UART0->D = 'b';
				while(!(UART0->S1 & UART0_S1_TDRE_MASK));
				UART0->D = '\r';
				while(!(UART0->S1 & UART0_S1_TDRE_MASK));
				UART0->D = '\n';
				ADC_Channel = 11;
			}
			if (rx_buf[0] == '2'){
				while(!(UART0->S1 & UART0_S1_TDRE_MASK));
				UART0->D = 'c';
				while(!(UART0->S1 & UART0_S1_TDRE_MASK));
				UART0->D = '\r';
				while(!(UART0->S1 & UART0_S1_TDRE_MASK));
				UART0->D = '\n';
				ADC_Channel = 10;
			}
			if (rx_buf[0] == '3'){
				while(!(UART0->S1 & UART0_S1_TDRE_MASK));
				UART0->D = 'd';
				while(!(UART0->S1 & UART0_S1_TDRE_MASK));
				UART0->D = '\r';
				while(!(UART0->S1 & UART0_S1_TDRE_MASK));
				UART0->D = '\n';
				ADC_Channel = 3;
			}
			if (rx_buf[0] == '4'){
				while(!(UART0->S1 & UART0_S1_TDRE_MASK));
				UART0->D = 'e';
				while(!(UART0->S1 & UART0_S1_TDRE_MASK));
				UART0->D = '\r';
				while(!(UART0->S1 & UART0_S1_TDRE_MASK));
				UART0->D = '\n';
				ADC_Channel = 12;
			}
			if (rx_buf[0] == '5'){
				while(!(UART0->S1 & UART0_S1_TDRE_MASK));
				UART0->D = 'f';
				while(!(UART0->S1 & UART0_S1_TDRE_MASK));
				UART0->D = '\r';
				while(!(UART0->S1 & UART0_S1_TDRE_MASK));
				UART0->D = '\n';
				ADC_Channel = 2;
			}
			if (rx_buf[0] == '6'){
				while(!(UART0->S1 & UART0_S1_TDRE_MASK));
				UART0->D = 'g';
				while(!(UART0->S1 & UART0_S1_TDRE_MASK));
				UART0->D = '\r';
				while(!(UART0->S1 & UART0_S1_TDRE_MASK));
				UART0->D = '\n';
				ADC_Channel = 13;
			}
			receive=0;
		}
	}
}
